import os
import json
import requests
from django.contrib.gis.geos import Point
from django.core.management import BaseCommand
from django.contrib.gis.db.models.functions import Distance

from api.models import VaccinationCenter, Osm22Po4Pgr
from api.utils.get_nearby_hotspot_cases import get_nearby_hotspot_cases


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

    help = "Populate vaccination centres from ppv.json (This may take a while)"

    def handle(self, *args, **options):
        current_dir = os.path.dirname(__file__)
        file_path = os.path.join(current_dir, 'ppv.json')

        with open(file_path, 'r') as json_data:
            data = json.load(json_data)
            for center in data['data']:
                # Create VaccinationCenter if does not exists
                try:
                    obj = VaccinationCenter.objects.get(name=center['ppvc'])
                except VaccinationCenter.DoesNotExist:
                    new_center = VaccinationCenter()
                    new_center.name = center['ppvc']
                    new_center.state = center['st']
                    new_center.district = center['dist']

                    if center['lon'] != "":
                        # Use the coordinate in ppv.json if exists
                        lng = float(center['lon'])
                        lat = float(center['lat'])
                    else:
                        # Use Google Place API to get coordinate
                        GOO_API_KEY = 'AIzaSyBIqj66yRMHmOfkgSRInnCB-dPD1Re0fcg'

                        res = requests.get(
                            f'https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input={new_center.name}&inputtype=textquery&fields=geometry&key={GOO_API_KEY}')
                        data = json.loads(res.text)

                        if not data['candidates']:
                            self.stdout.write(
                                f"Skipped {new_center.name} due to coordinates not found")
                            continue

                        lat = data['candidates'][0]['geometry']['location']['lat']
                        lng = data['candidates'][0]['geometry']['location']['lng']

                    new_center.location = Point(lng, lat, srid=4326)

                    # Find the nearest PPV's vertex id of OSM database for caching
                    vertex = Osm22Po4Pgr.objects.using('osm').filter(x1__range=[lng-0.1, lng+0.1]).annotate(
                        distance=Distance("geom_way", new_center.location)).order_by("distance")[0]

                    new_center.gid = vertex.target

                    # Update nearby cases
                    new_center.num_cases = get_nearby_hotspot_cases(lat, lng)

                    # Save to database
                    new_center.save()

                    self.stdout.write(f"Added {new_center.name} successfully")

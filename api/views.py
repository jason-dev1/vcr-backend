from django.db import connections
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.utils import timezone
from django.contrib.gis.geos import GEOSGeometry
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from .models import Account, Appointment, Osm22Po4Pgr, VaccinationCenter, VaxMalaysia, VaccinationTimeslot, VaccinationRecord
from .serializers import AccountSerializer, AppointmentSerializer,  CustomTokenObtainPairSerializer, MakeAppointmentSerializer, UpdateAppointmentSerializer, VaccinationCenterSerializer, VaccinationTimeslotSerializer, VaccinationRecordSerializer, VaxMalaysiaSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class AppointmentViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'head', 'options']
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        # Find all appointments
        account = Account.objects.get(user_id=self.request.user.id)
        appointments = Appointment.objects.filter(account=account)

        next_dose_type = Appointment.DOSE_TYPE_FIRST

        for appointment in appointments:
            if 0 < appointment.appointment_status < Appointment.APPOINTMENT_STATUS_ATTENDED:
                # Return error if there is any ongoing appointment
                return Response({'detail': 'Appointment failed to create due to ongoing appointment exists.'}, status=status.HTTP_400_BAD_REQUEST)

            elif appointment.appointment_status == Appointment.APPOINTMENT_STATUS_ATTENDED:
                # Set dose for next appointment, e.g. taken first dose, next appointment is second dose
                if appointment.dose_type >= next_dose_type:
                    next_dose_type = appointment.dose_type + 1

        if next_dose_type > Appointment.DOSE_TYPE_BOOSTER:
            # Return error if dose limit reached (Taken booster dose)
            return Response({'detail': 'You are not eligible for making appointment.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = MakeAppointmentSerializer(
            data=request.data,
            context={'user_id': self.request.user.id})
        serializer.is_valid(raise_exception=True)
        appointment = serializer.save(dose_type=next_dose_type)
        serializer = AppointmentSerializer(appointment)
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        if request.data['appointment_status'] == Appointment.APPOINTMENT_STATUS_CANCELLED:
            """Cancel appointment"""
            if Appointment.APPOINTMENT_STATUS_PENDING <= Appointment.objects.get(id=kwargs['pk']).appointment_status <= Appointment.APPOINTMENT_STATUS_APPROVED:
                return super().partial_update(request, *args, **kwargs)

        return Response({'detail': 'Appointment status failed to update due to invalid state.'}, status=status.HTTP_400_BAD_REQUEST)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return MakeAppointmentSerializer
        elif self.request.method == 'PATCH':
            return UpdateAppointmentSerializer
        return AppointmentSerializer

    def get_queryset(self):
        user = self.request.user

        account_id = Account.objects.only(
            'id').get(user_id=user.id)

        return Appointment.objects.filter(account_id=account_id).order_by('-last_updated_datetime')


class AccountViewSet(GenericViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['GET', 'PUT'])
    def me(self, request):
        """Fetch/Update personal account details"""
        account = Account.objects.get(user_id=request.user.id)

        if request.method == 'GET':
            serializer = AccountSerializer(account)
            return Response(serializer.data)
        elif request.method == 'PUT':
            account = Account.objects.get(user_id=request.user.id)
            serializer = AccountSerializer(account, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)


class VaccinationCenterViewSet(GenericViewSet):
    queryset = VaccinationCenter.objects.all()
    serializer_class = VaccinationCenterSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['GET'], url_path='nearby/(?P<latitude>\d+\.\d+),(?P<longitude>\d+\.\d+)')
    def nearby(self, request, latitude, longitude):
        """Get nearby center list using shortest path calculation"""

        def dictfetchall(cursor):
            """Return all rows from a cursor as a dict"""
            columns = [col[0] for col in cursor.description]
            return [
                dict(zip(columns, row))
                for row in cursor.fetchall()
            ]

        # Create Point object from coordinates
        longitude = float(longitude)
        latitude = float(latitude)
        user_location = Point(longitude, latitude, srid=4326)

        # Get user's nearest OSM source vertex id from OSM database
        user_osm_vertex = Osm22Po4Pgr.objects.using('osm').filter(
            x1__range=[longitude-0.001, longitude+0.001]).annotate(
                distance=Distance("geom_way", user_location)).order_by("distance")[0]

        user_gid = user_osm_vertex.source

        # Get user's district by seaching nearby vaccination center by querying VCR database, e.g. Cyberjaya
        vaccination_center = VaccinationCenter.objects.annotate(
            distance=Distance("location", user_location)).order_by("distance")[0]

        district = vaccination_center.district

        # Find all centers which are same district as user's location, e.g. All centers in Cyberjaya
        vaccination_centers = VaccinationCenter.objects.filter(
            district=district).filter(gid__gte=0)

        # Find nearby vaccination center list with paths sorted by distance
        with connections['osm'].cursor() as cursor:
            cursor.execute('''
            WITH result AS (
                SELECT seq,
                    '(' || start_vid || ',' || end_vid || ')' AS path_name,
                    path_seq, start_vid, end_vid, node, edge, cost,
                    lead(agg_cost) over() AS agg_cost
                FROM pgr_dijkstra('SELECT id, source, target, cost FROM osm2_2po_4pgr',
                    %s,
                    %s,
                    directed := FALSE)),

                with_geom AS
                    (SELECT seq, result.path_name, CASE
                        WHEN result.node = osm2_2po_4pgr.source
                            THEN osm2_2po_4pgr.geom_way
                        ELSE ST_Reverse(osm2_2po_4pgr.geom_way)
                        END AS path_geom
                    FROM osm2_2po_4pgr 
                        JOIN result ON osm2_2po_4pgr.id = result.edge),

                one_geom AS 
                    (SELECT path_name, ST_LineMerge(ST_Union(path_geom)) AS path_geom 
                        FROM with_geom GROUP BY path_name ORDER BY path_name),

                aggregates AS 
                    (SELECT path_name, start_vid, end_vid, SUM(cost) AS agg_cost 
                        FROM result GROUP BY path_name, start_vid, end_vid
                        ORDER BY start_vid, end_vid)

            SELECT end_vid AS gid, agg_cost, path_geom
                FROM aggregates JOIN one_geom USING (path_name) ORDER BY agg_cost''',
                           [[user_gid], list(vaccination_centers.values_list("gid"))])

            rows = dictfetchall(cursor)

        # Post-processing json data for client's response
        for row in rows:
            geom = GEOSGeometry(row['path_geom'])
            center = vaccination_centers.get(gid=row['gid'])
            row['id'] = center.id
            row['distance'] = round(row['agg_cost'], 3)
            row['cases'] = center.num_cases
            row['name'] = center.name
            row['district'] = center.district
            row['state'] = center.state
            row['lat'] = round(center.location.coords[1], 5)
            row['lng'] = round(center.location.coords[0], 5)
            row['path'] = geom.coords
            row.pop("agg_cost")
            row.pop("gid")
            row.pop("path_geom")

        return Response(rows)


class VaccinationTimeslotViewSet(ListModelMixin, GenericViewSet):
    serializer_class = VaccinationTimeslotSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return VaccinationTimeslot.objects.filter(center_id=self.kwargs['center_pk'], datetime__gte=timezone.now())


class VaccinationRecordViewSet(ListModelMixin, GenericViewSet):
    queryset = VaccinationRecord.objects.all()
    serializer_class = VaccinationRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        account_id = Account.objects.only(
            'id').get(user_id=user.id)

        appointments = Appointment.objects.filter(account_id=account_id)

        return VaccinationRecord.objects.filter(appointment__in=appointments)


class VaxMalaysiaViewSet(ListModelMixin, GenericViewSet):
    queryset = VaxMalaysia.objects.order_by('-date')
    serializer_class = VaxMalaysiaSerializer
    permission_classes = [IsAuthenticated]

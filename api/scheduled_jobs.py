import csv
import requests
from datetime import datetime, timedelta, timezone
from django.utils import timezone
from .models import Appointment, VaxMalaysia, VaccinationCenter
from .utils.get_nearby_hotspot_cases import get_nearby_hotspot_cases


def update_statistic_data():
    """Update vaccination statistic data by fetching from GitHub repo"""
    print("Updating vaccination statistic data from GitHub")
    download = requests.get(
        'https://raw.githubusercontent.com/CITF-Malaysia/citf-public/main/vaccination/vax_malaysia.csv')

    decoded_content = download.content.decode('utf-8')

    cr = csv.reader(decoded_content.splitlines(), delimiter=',')
    next(cr)
    for row in cr:
        _, created = VaxMalaysia.objects.update_or_create(
            date=row[0],
            defaults={
                'daily_partial': row[1],
                'daily_full': row[2],
                'daily_booster': row[3],
                'daily': row[4],
                'cumul_partial': row[9],
                'cumul_full': row[10],
                'cumul_booster': row[11],
                'cumul': row[12], }
        )

    print("Updated vaccination statistic data")


def update_centers_hotspot_case():
    """Update vaccination center hotspot cases data by fetching from MySj API"""
    print("Updating vaccination centers hotspot data")

    vaccination_centers = VaccinationCenter.objects.all()

    for center in vaccination_centers:
        id = center.id
        lat = center.location.coords[1]
        lng = center.location.coords[0]
        last_updated = center.last_updated_datetime

        if (datetime.now(timezone.utc) - last_updated) > timedelta(hours=24):
            num_cases = get_nearby_hotspot_cases(lat, lng)

            VaccinationCenter.objects.update_or_create(
                id=id, defaults={'num_cases': num_cases})

    print("Updated vaccination centers hotspot data")


def update_appointment_status():
    """Update appointment status for overdue appointments"""
    print("Updating appointment status")

    appointments = Appointment.objects.filter(
        appointment_status__gte=Appointment.APPOINTMENT_STATUS_PENDING)

    for appointment in appointments:
        id = appointment.id
        status = appointment.appointment_status
        appointment_datetime = timezone.make_naive(
            appointment.timeslot.datetime)
        now_datetime = datetime.now()

        if appointment_datetime <= now_datetime:
            if status == Appointment.APPOINTMENT_STATUS_APPROVED:
                """Appointment expired - Update state to MISSED"""
                Appointment.objects.update_or_create(
                    id=id, defaults={'appointment_status': Appointment.APPOINTMENT_STATUS_MISSED})

            elif status == Appointment.APPOINTMENT_STATUS_PENDING:
                """Appointment expired - Update state to REJECTED for pending appointment"""
                Appointment.objects.update_or_create(
                    id=id, defaults={'appointment_status': Appointment.APPOINTMENT_STATUS_REJECTED})

        return

    print("Updated appointment status")

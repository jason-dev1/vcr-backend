import api.scheduled_jobs as scheduled_jobs
from django.core.management import BaseCommand


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

    help = "Run scheduled jobs immediately"

    def handle(self, *args, **options):
        scheduled_jobs.update_statistic_data()
        scheduled_jobs.update_appointment_status()
        scheduled_jobs.update_centers_hotspot_case()

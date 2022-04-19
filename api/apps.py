from django.apps import AppConfig
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

    def ready(self) -> None:
        import api.scheduled_jobs as scheduled_jobs
        import api.signals.handlers

        # Schedule tasks to run on 12a.m. every day
        scheduler = BackgroundScheduler()
        trigger = CronTrigger(hour=0, minute=0, second=0)
        scheduler.add_job(scheduled_jobs.update_statistic_data, trigger)
        scheduler.add_job(scheduled_jobs.update_appointment_status, trigger)
        scheduler.add_job(scheduled_jobs.update_centers_hotspot_case, trigger)
        scheduler.start()

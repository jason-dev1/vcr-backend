import json
from django.conf import settings
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from api.models import Account, Appointment, VaccinationRecord
from api.serializers import AppointmentSerializer
from api.utils.send_push_message import send_push_message


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_account_for_new_user(sender, **kwargs):
    if kwargs['created']:
        Account.objects.create(user=kwargs['instance'])


@receiver(pre_save, sender=Appointment)
def push_notification_after_appointment_approved_or_rejected(sender, instance,  **kwargs):
    """Push notification whenever an appointment is approved or rejected"""
    if instance.id is None:
        pass
    else:
        previous = Appointment.objects.get(id=instance.id)
        token = previous.account.expo_notification_token

        if token == '':
            return

        body = 'Appointment Notification'
        title = 'Appointment Notification Body'

        appointment_obj = AppointmentSerializer(instance).data
        serialized_appointment_obj = json.dumps(appointment_obj, default=str)

        if previous.appointment_status == Appointment.APPOINTMENT_STATUS_PENDING and instance.appointment_status == Appointment.APPOINTMENT_STATUS_APPROVED:
            title = 'Appointment APPROVED!'
            body = 'Congratulation, your appointment is approved. Please click here to view your appointment details.'

        elif previous.appointment_status == Appointment.APPOINTMENT_STATUS_PENDING and instance.appointment_status == Appointment.APPOINTMENT_STATUS_REJECTED:
            title = 'Appointment REJECTED!'
            body = 'Sorry, your appointment is rejected. You may submit a new appointment again.'

        else:
            return

        send_push_message(token, title, body, serialized_appointment_obj)


@receiver(pre_save, sender=VaccinationRecord)
def push_notification_after_record_added(sender, instance,  **kwargs):
    """Push notification whenever a vaccination record is inserted"""
    if instance.id is None:
        token = instance.appointment.account.expo_notification_token

        if token == '':
            return

        dose_type_string = dict(Appointment.DOSE_TYPE_CHOICES)[
            instance.appointment.dose_type].upper()

        send_push_message(token, f'{dose_type_string} dose received!',
                          f'Congratulation, you have received your {dose_type_string} vaccination dose. Please click here to view your vaccination details.')


@receiver(pre_save, sender=VaccinationRecord)
def update_appointment_status_after_record_added(sender, instance,  **kwargs):
    """Update appointment status to ATTENDED whenever a vaccination record is inserted"""
    if instance.id is None:
        if instance.appointment.appointment_status != Appointment.APPOINTMENT_STATUS_ATTENDED:
            updated_appointment = instance.appointment
            updated_appointment.appointment_status = Appointment.APPOINTMENT_STATUS_ATTENDED
            Appointment.save(updated_appointment, force_update=True)

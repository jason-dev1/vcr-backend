import datetime
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib import admin, messages
from django.contrib.admin.filters import DateFieldListFilter
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.gis.admin import GISModelAdmin
from django.db.models import Q

from .models import Account, Appointment, User, VaccinationCenter,  VaccinationRecord, VaccinationTimeslot

admin.site.disable_action('delete_selected')


class CustomDateFieldListFilter(DateFieldListFilter):
    """Custom date field list filter for timeslot"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        today = datetime.date.today()
        yesterday = today - datetime.timedelta(days=1)
        tomorrow = today + datetime.timedelta(days=1)

        self.links = list(self.links)
        self.links.insert(0, ('Yesterday', {
            self.lookup_kwarg_since: str(yesterday),
            self.lookup_kwarg_until: str(today),
        }))

        self.links.insert(0, ("Tomorrow", {
            self.lookup_kwarg_since: str(tomorrow),
            self.lookup_kwarg_until: str(tomorrow + + datetime.timedelta(days=1)),
        }))

        self.links.insert(0, ("Next 7 days", {
            self.lookup_kwarg_since: str(today),
            self.lookup_kwarg_until: str(today + datetime.timedelta(days=7)),
        }))


class AccountInline(admin.StackedInline):
    model = Account
    min_num = 1
    max_num = 1


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """Define admin model for custom User model with no email field."""

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    inlines = [AccountInline]
    list_display = ['email', 'name', 'date_of_birth', 'ic_number',
                    'country', 'state', 'assigned_vaccination_center']
    list_select_related = ['account']
    search_fields = ['email', 'account__name', 'account__ic_number']
    ordering = ['-date_joined']

    def save_formset(self, request, form, formset, change) -> None:
        return super().save_formset(request, form, formset, change)

    @admin.display(description='Name', ordering='account__name')
    def name(self, obj):
        return (obj.account.name)

    @admin.display(description='D.O.B.', ordering='account__date_of_birth')
    def date_of_birth(self, obj):
        return (obj.account.date_of_birth)

    @admin.display(description='IC Number', ordering='account__ic_number')
    def ic_number(self, obj):
        return (obj.account.ic_number)

    @admin.display(description='Country', ordering='account__country')
    def country(self, obj):
        return (obj.account.country)

    @admin.display(description='State', ordering='account__state')
    def state(self, obj):
        return (obj.account.state)

    @admin.display(description='Assigned Vax Center', ordering='account__assigned_vaccination_center__name')
    def assigned_vaccination_center(self, obj):
        return (obj.account.assigned_vaccination_center)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            account = Account.objects.get(user_id=instance.user_id)
            instance.id = account.id
            instance.save(force_update=True)
        formset.save_m2m()


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    actions = ['approve_appointment', 'reject_appointment']
    list_display = ['id', 'account', 'timeslot',
                    'appointment_status', 'dose_type', 'last_updated_datetime_formatted']
    list_filter = ['appointment_status', 'dose_type', 'timeslot']
    ordering = ['-last_updated_datetime']
    search_fields = ['account__name', 'timeslot__center__name']

    @admin.display(description='Last updated', ordering='last_updated_datetime')
    def last_updated_datetime_formatted(self, obj):
        return timezone.make_naive(obj.last_updated_datetime).strftime("%Y-%m-%d_%H:%M")

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if request.user.is_superuser != True:
            account = Account.objects.get(user=request.user)

            if(account.assigned_vaccination_center):
                return qs.filter(timeslot__center=account.assigned_vaccination_center)

        return qs

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser != True:
            if obj:
                return self.readonly_fields + ('account', )

        return self.readonly_fields

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if request.user.is_superuser != True:
            if db_field.name == "appointment_status":
                appointment = Appointment.objects.get(
                    id=request.resolver_match.kwargs['object_id'])
                status = appointment.appointment_status

                kwargs['choices'] = (
                    (status, dict(Appointment.APPOINTMENT_STATUS_CHOICES)[status]),)

                if(status == Appointment.APPOINTMENT_STATUS_PENDING):
                    kwargs['choices'] += (
                        (Appointment.APPOINTMENT_STATUS_APPROVED, 'Approved'),
                        (Appointment.APPOINTMENT_STATUS_REJECTED, 'Rejected'))

                elif(status == Appointment.APPOINTMENT_STATUS_APPROVED):
                    kwargs['choices'] += (
                        (Appointment.APPOINTMENT_STATUS_ATTENDED, 'Attended'),
                        (Appointment.APPOINTMENT_STATUS_MISSED, 'Missed'))

        return super().formfield_for_choice_field(db_field, request, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if request.user.is_superuser != True:
            if db_field.name == "timeslot":
                account = Account.objects.get(user=request.user)
                kwargs["queryset"] = VaccinationTimeslot.objects.filter(
                    center=account.assigned_vaccination_center)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    @ admin.action(description='Approve appointment')
    def approve_appointment(self, request, queryset):
        for obj in queryset:
            if(obj.appointment_status == Appointment.APPOINTMENT_STATUS_PENDING):
                obj.appointment_status = Appointment.APPOINTMENT_STATUS_APPROVED
                Appointment.save(obj)
                self.message_user(
                    request,
                    f'Appointment ID: {obj.id} was successfully approved.',
                    messages.SUCCESS
                )

            else:
                self.message_user(
                    request,
                    f'Appointment ID: {obj.id} was failed to approve.',
                    messages.ERROR
                )

    @ admin.action(description='Reject appointment')
    def reject_appointment(self, request, queryset):
        for obj in queryset:
            if(obj.appointment_status == Appointment.APPOINTMENT_STATUS_PENDING):
                obj.appointment_status = Appointment.APPOINTMENT_STATUS_REJECTED
                Appointment.save(obj)
                self.message_user(
                    request,
                    f'Appointment ID: {obj.id} was successfully rejected.',
                    messages.SUCCESS
                )

            else:
                self.message_user(
                    request,
                    f'Appointment ID: {obj.id} was failed to reject.',
                    messages.ERROR
                )


@ admin.register(VaccinationCenter)
class VaccinationCenterAdmin(GISModelAdmin):
    list_display = ['name', 'state', 'district', 'num_cases', 'lat', 'lon']
    list_filter = ['state', 'district']
    ordering = ['name']
    search_fields = ['name', 'state', 'district']

    @ admin.display(description='Latitude')
    def lat(self, obj):
        return (obj.location.coords[1])

    @ admin.display(description='Longtitude')
    def lon(self, obj):
        return (obj.location.coords[0])


@ admin.register(VaccinationRecord)
class VaccinationRecordAdmin(admin.ModelAdmin):
    list_display = ['id', 'dose_receive_datetime_formatted',
                    'vaccine_brand', 'appointment']
    list_display_links = ["id", "dose_receive_datetime_formatted"]
    list_filter = ['vaccine_brand']
    ordering = ['-dose_receive_datetime']
    search_fields = ['appointment__account__name', 'dose_receive_datetime']

    @ admin.display(description='Dose receive datetime', ordering='dose_receive_datetime')
    def dose_receive_datetime_formatted(self, obj):
        return timezone.make_naive(obj.dose_receive_datetime).strftime("%Y-%m-%d_%H:%M")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        existing_appointment_record_ids = VaccinationRecord.objects.values_list(
            'appointment_id', flat=True)

        if db_field.name == "appointment":
            queryset = Appointment.objects.filter(
                ~Q(id__in=existing_appointment_record_ids),
                Q(appointment_status__gte=Appointment.APPOINTMENT_STATUS_APPROVED))

            if request.user.is_superuser != True:
                account = Account.objects.get(user=request.user)
                queryset = queryset.filter(
                    Q(timeslot__center=account.assigned_vaccination_center)
                )

            kwargs["queryset"] = queryset

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if request.user.is_superuser != True:
            account = Account.objects.get(user=request.user)

            if(account.assigned_vaccination_center):
                return qs.filter(appointment__timeslot__center=account.assigned_vaccination_center)

        return qs


@ admin.register(VaccinationTimeslot)
class VaccinationTimeslotAdmin(admin.ModelAdmin):
    list_display = ('id', 'datetime_formatted', 'center')
    list_display_links = ["id", "datetime_formatted"]
    list_filter = ['center', ('datetime', CustomDateFieldListFilter)]
    ordering = ['-datetime']
    search_fields = ['center__name', 'datetime']

    @ admin.display(description='Timeslot datetime', ordering='datetime')
    def datetime_formatted(self, obj):
        return timezone.make_naive(obj.datetime).strftime("%Y-%m-%d_%H:%M")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if request.user.is_superuser != True:
            account = Account.objects.get(user=request.user)
            kwargs["queryset"] = VaccinationCenter.objects.filter(
                id=account.assigned_vaccination_center_id)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if request.user.is_superuser != True:
            account = Account.objects.get(user=request.user)
            if(account.assigned_vaccination_center):
                return qs.filter(center=account.assigned_vaccination_center)

        return qs

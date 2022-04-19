from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.contrib.gis.db import models
from django.forms import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Custom User Model - Use email for authorization instead of username field."""

    objects = UserManager()
    username = None
    email = models.EmailField(_('email address'), unique=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []


class Account(models.Model):
    """Account model"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    name = models.CharField(max_length=100, blank=True)
    ic_number = models.CharField(max_length=12, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    country = models.CharField(max_length=50, blank=True)
    state = models.CharField(max_length=50, blank=True)
    expo_notification_token = models.CharField(max_length=50, blank=True)
    assigned_vaccination_center = models.ForeignKey(
        'VaccinationCenter', on_delete=models.PROTECT, blank=True, null=True)

    def __str__(self):
        return f'{self.name}'

    def email(self):
        return self.user.email


class VaccinationCenter(models.Model):
    """Vaccination Center model"""
    name = models.CharField(max_length=255)
    location = models.PointField(null=True)
    state = models.CharField(max_length=50)
    district = models.CharField(max_length=50)
    num_cases = models.IntegerField(default=0)
    gid = models.IntegerField(default=0)
    last_updated_datetime = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.name}'


class VaccinationTimeslot(models.Model):
    """Vaccination Timeslot model"""
    def validate_datetime_future(datetime):
        if datetime < timezone.now():
            raise ValidationError("Datetime must be in the future")

    datetime = models.DateTimeField(validators=[validate_datetime_future])
    center = models.ForeignKey(VaccinationCenter, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.center}_{timezone.make_naive(self.datetime).strftime("%Y-%m-%d_%H:%M")}'


class Appointment(models.Model):
    """Appointment model"""
    APPOINTMENT_STATUS_PENDING = 1
    APPOINTMENT_STATUS_APPROVED = 2
    APPOINTMENT_STATUS_ATTENDED = 3
    APPOINTMENT_STATUS_CANCELLED = -1
    APPOINTMENT_STATUS_REJECTED = -2
    APPOINTMENT_STATUS_MISSED = -3
    APPOINTMENT_STATUS_CHOICES = [
        (APPOINTMENT_STATUS_APPROVED, 'Approved'),
        (APPOINTMENT_STATUS_ATTENDED, 'Attended'),
        (APPOINTMENT_STATUS_CANCELLED, 'Cancelled'),
        (APPOINTMENT_STATUS_MISSED, 'Missed'),
        (APPOINTMENT_STATUS_PENDING, 'Pending'),
        (APPOINTMENT_STATUS_REJECTED, 'Rejected')
    ]
    appointment_status = models.IntegerField(
        choices=APPOINTMENT_STATUS_CHOICES,
        default=APPOINTMENT_STATUS_PENDING)
    DOSE_TYPE_FIRST = 1
    DOSE_TYPE_SECOND = 2
    DOSE_TYPE_BOOSTER = 3
    DOSE_TYPE_CHOICES = [
        (DOSE_TYPE_FIRST, 'First'),
        (DOSE_TYPE_SECOND, 'Second'),
        (DOSE_TYPE_BOOSTER, 'Booster'),
    ]

    dose_type = models.IntegerField(choices=DOSE_TYPE_CHOICES)
    last_updated_datetime = models.DateTimeField(auto_now=True)
    account = models.ForeignKey(Account, on_delete=models.PROTECT)
    timeslot = models.ForeignKey(
        VaccinationTimeslot, on_delete=models.PROTECT)

    def __str__(self):
        return f'{self.account}_{dict(self.APPOINTMENT_STATUS_CHOICES)[self.appointment_status]}_{dict(self.DOSE_TYPE_CHOICES)[self.dose_type]} Dose'


class VaccinationRecord(models.Model):
    """Vaccination Record model"""
    VACCINE_BRAND_PFIZER = 1
    VACCINE_BRAND_SINOVAC = 2
    VACCINE_BRAND_ASTRAZENECA = 3
    VACCINE_BRAND_CANSINO = 4
    VACCINE_BRAND_CHOICES = [
        (VACCINE_BRAND_PFIZER, 'Pfizer'),
        (VACCINE_BRAND_SINOVAC, 'Sinovac'),
        (VACCINE_BRAND_ASTRAZENECA, 'AstraZeneca'),
        (VACCINE_BRAND_CANSINO, 'Cansino'),
    ]

    dose_receive_datetime = models.DateTimeField(auto_now_add=True)
    vaccine_brand = models.IntegerField(choices=VACCINE_BRAND_CHOICES)
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.appointment} {dict(self.VACCINE_BRAND_CHOICES)[self.vaccine_brand]}'


class Osm22Po4Pgr(models.Model):
    """For OSM pgRouting data model (Non-managed model)"""
    id = models.IntegerField(primary_key=True)
    osm_id = models.BigIntegerField(blank=True, null=True)
    osm_name = models.CharField(max_length=255, blank=True, null=True)
    osm_meta = models.CharField(max_length=255, blank=True, null=True)
    osm_source_id = models.BigIntegerField(blank=True, null=True)
    osm_target_id = models.BigIntegerField(blank=True, null=True)
    clazz = models.IntegerField(blank=True, null=True)
    flags = models.IntegerField(blank=True, null=True)
    source = models.IntegerField(blank=True, null=True)
    target = models.IntegerField(blank=True, null=True)
    km = models.FloatField(blank=True, null=True)
    kmh = models.IntegerField(blank=True, null=True)
    cost = models.FloatField(blank=True, null=True)
    reverse_cost = models.FloatField(blank=True, null=True)
    x1 = models.FloatField(blank=True, null=True)
    y1 = models.FloatField(blank=True, null=True)
    x2 = models.FloatField(blank=True, null=True)
    y2 = models.FloatField(blank=True, null=True)
    geom_way = models.LineStringField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'osm2_2po_4pgr'


class VaxMalaysia(models.Model):
    """Vaccination Center model"""
    date = models.DateField(primary_key=True)
    daily_partial = models.IntegerField()
    daily_full = models.IntegerField()
    daily_booster = models.IntegerField()
    daily = models.IntegerField()
    cumul_partial = models.IntegerField()
    cumul_full = models.IntegerField()
    cumul_booster = models.IntegerField()
    cumul = models.IntegerField()

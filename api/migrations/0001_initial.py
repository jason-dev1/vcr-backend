# Generated by Django 4.0.3 on 2022-04-19 14:40

import api.models
from django.conf import settings
import django.contrib.gis.db.models.fields
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Osm22Po4Pgr',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('osm_id', models.BigIntegerField(blank=True, null=True)),
                ('osm_name', models.CharField(blank=True, max_length=255, null=True)),
                ('osm_meta', models.CharField(blank=True, max_length=255, null=True)),
                ('osm_source_id', models.BigIntegerField(blank=True, null=True)),
                ('osm_target_id', models.BigIntegerField(blank=True, null=True)),
                ('clazz', models.IntegerField(blank=True, null=True)),
                ('flags', models.IntegerField(blank=True, null=True)),
                ('source', models.IntegerField(blank=True, null=True)),
                ('target', models.IntegerField(blank=True, null=True)),
                ('km', models.FloatField(blank=True, null=True)),
                ('kmh', models.IntegerField(blank=True, null=True)),
                ('cost', models.FloatField(blank=True, null=True)),
                ('reverse_cost', models.FloatField(blank=True, null=True)),
                ('x1', models.FloatField(blank=True, null=True)),
                ('y1', models.FloatField(blank=True, null=True)),
                ('x2', models.FloatField(blank=True, null=True)),
                ('y2', models.FloatField(blank=True, null=True)),
                ('geom_way', django.contrib.gis.db.models.fields.LineStringField(blank=True, null=True, srid=4326)),
            ],
            options={
                'db_table': 'osm2_2po_4pgr',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('email', models.EmailField(max_length=254, unique=True, verbose_name='email address')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            managers=[
                ('objects', api.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=100)),
                ('ic_number', models.CharField(blank=True, max_length=12)),
                ('date_of_birth', models.DateField(blank=True, null=True)),
                ('country', models.CharField(blank=True, max_length=50)),
                ('state', models.CharField(blank=True, max_length=50)),
                ('expo_notification_token', models.CharField(blank=True, max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='Appointment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('appointment_status', models.IntegerField(choices=[(2, 'Approved'), (3, 'Attended'), (-1, 'Cancelled'), (-3, 'Missed'), (1, 'Pending'), (-2, 'Rejected')], default=1)),
                ('dose_type', models.IntegerField(choices=[(1, 'First'), (2, 'Second'), (3, 'Booster')])),
                ('last_updated_datetime', models.DateTimeField(auto_now=True)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='api.account')),
            ],
        ),
        migrations.CreateModel(
            name='VaccinationCenter',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('location', django.contrib.gis.db.models.fields.PointField(null=True, srid=4326)),
                ('state', models.CharField(max_length=50)),
                ('district', models.CharField(max_length=50)),
                ('num_cases', models.IntegerField(default=0)),
                ('gid', models.IntegerField(default=0)),
                ('last_updated_datetime', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='VaxMalaysia',
            fields=[
                ('date', models.DateField(primary_key=True, serialize=False)),
                ('daily_partial', models.IntegerField()),
                ('daily_full', models.IntegerField()),
                ('daily_booster', models.IntegerField()),
                ('daily', models.IntegerField()),
                ('cumul_partial', models.IntegerField()),
                ('cumul_full', models.IntegerField()),
                ('cumul_booster', models.IntegerField()),
                ('cumul', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='VaccinationTimeslot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datetime', models.DateTimeField(validators=[api.models.VaccinationTimeslot.validate_datetime_future])),
                ('center', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.vaccinationcenter')),
            ],
        ),
        migrations.CreateModel(
            name='VaccinationRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dose_receive_datetime', models.DateTimeField(auto_now_add=True)),
                ('vaccine_brand', models.IntegerField(choices=[(1, 'Pfizer'), (2, 'Sinovac'), (3, 'AstraZeneca'), (4, 'Cansino')])),
                ('appointment', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='api.appointment')),
            ],
        ),
        migrations.AddField(
            model_name='appointment',
            name='timeslot',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='api.vaccinationtimeslot'),
        ),
        migrations.AddField(
            model_name='account',
            name='assigned_vaccination_center',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='api.vaccinationcenter'),
        ),
        migrations.AddField(
            model_name='account',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]

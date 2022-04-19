from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from djoser.serializers import UserSerializer as BaseUserSerializer, UserCreateSerializer as BaseUserCreateSerializer
from .models import Account, Appointment, VaccinationCenter, VaccinationTimeslot, VaccinationRecord, VaxMalaysia


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Override TokenObtainPair to include email inside the token payload"""
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        return token


class UserCreateSerializer(BaseUserCreateSerializer):
    class Meta(BaseUserCreateSerializer.Meta):
        fields = ['id', 'email', 'password']


class UserSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        fields = ['id', 'email', 'is_superuser', 'is_staff', 'is_active']
        ref_name = "UserSerializer"


class AccountSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Account
        fields = ['id', 'user_id', 'name', 'date_of_birth', 'ic_number',
                  'country', 'state', 'expo_notification_token']

    def create(self, validated_data):
        user = self.context['request'].user
        return Account.objects.create(
            user=user, **validated_data)


class VaccinationCenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = VaccinationCenter
        fields = ['id', 'name', 'location', 'state', 'district']
        geo_field = "point"


class VaccinationTimeslotSerializer(serializers.ModelSerializer):
    center = VaccinationCenterSerializer()

    class Meta:
        model = VaccinationTimeslot
        fields = ['id', 'datetime', 'center']


class AppointmentSerializer(serializers.ModelSerializer):
    account = AccountSerializer()
    timeslot = VaccinationTimeslotSerializer()

    class Meta:
        model = Appointment
        fields = ['id', 'account', 'timeslot', 'appointment_status',
                  'dose_type', 'last_updated_datetime']


class MakeAppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ['id', 'timeslot']

    def create(self, validated_data):
        account = Account.objects.get(user_id=self.context['user_id'])
        return Appointment.objects.create(
            account=account, **validated_data)


class UpdateAppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ['appointment_status']


class VaccinationRecordSerializer(serializers.ModelSerializer):
    appointment = AppointmentSerializer()

    class Meta:
        model = VaccinationRecord
        fields = ['id', 'dose_receive_datetime',
                  'vaccine_brand', 'appointment']


class VaxMalaysiaSerializer(serializers.ModelSerializer):
    class Meta:
        model = VaxMalaysia
        fields = ['date', 'daily_partial', 'daily_full', 'daily_booster',
                  'daily', 'cumul_partial', 'cumul_full', 'cumul_booster', 'cumul']

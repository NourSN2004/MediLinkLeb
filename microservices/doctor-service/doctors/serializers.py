"""
Doctor Service Serializers
Handles serialization and inter-service communication
"""
from rest_framework import serializers
from .models import Doctor, DoctorWorkingHours, DoctorTimeOff
import requests
from django.conf import settings


def get_user_info(user_id):
    """
    Fetch user information from Auth Service
    Returns user data or None if request fails
    """
    try:
        response = requests.get(
            f"{settings.AUTH_SERVICE_URL}/api/auth/users/{user_id}/",
            headers={'X-Service-Auth': settings.SERVICE_SECRET_KEY},
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error fetching user info: {e}")
    return None


class DoctorWorkingHoursSerializer(serializers.ModelSerializer):
    """Serializer for doctor working hours"""

    day_name = serializers.CharField(source='get_day_of_week_display', read_only=True)

    class Meta:
        model = DoctorWorkingHours
        fields = ['id', 'day_of_week', 'day_name', 'start_time', 'end_time']

    def validate(self, data):
        """Ensure start_time is before end_time"""
        if data.get('start_time') and data.get('end_time'):
            if data['start_time'] >= data['end_time']:
                raise serializers.ValidationError({
                    "end_time": "End time must be after start time"
                })
        return data


class DoctorTimeOffSerializer(serializers.ModelSerializer):
    """Serializer for doctor time-off"""

    class Meta:
        model = DoctorTimeOff
        fields = ['id', 'date', 'start_time', 'end_time', 'reason']

    def validate(self, data):
        """Ensure start_time is before end_time"""
        if data.get('start_time') and data.get('end_time'):
            if data['start_time'] >= data['end_time']:
                raise serializers.ValidationError({
                    "end_time": "End time must be after start time"
                })
        return data


class DoctorSerializer(serializers.ModelSerializer):
    """
    Serializer for Doctor with nested working hours and time-off
    Includes user information from Auth Service
    """

    # User information from Auth Service (read-only)
    user_info = serializers.SerializerMethodField()

    # Nested relationships
    working_hours = DoctorWorkingHoursSerializer(many=True, read_only=True)
    time_off = DoctorTimeOffSerializer(many=True, read_only=True)

    class Meta:
        model = Doctor
        fields = [
            'user_id',
            'specialty',
            'license_number',
            'user_info',
            'working_hours',
            'time_off',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['user_id', 'created_at', 'updated_at']

    def get_user_info(self, obj):
        """Fetch user details from Auth Service"""
        user_data = get_user_info(obj.user_id)
        if user_data:
            return {
                'id': user_data.get('id'),
                'email': user_data.get('email'),
                'name': user_data.get('name'),
                'phone_number': user_data.get('phone_number'),
                'role': user_data.get('role')
            }
        return None


class DoctorCreateSerializer(serializers.Serializer):
    """
    Serializer for creating a doctor profile
    Requires user_id to already exist in Auth Service with role='doctor'
    """
    user_id = serializers.IntegerField()
    specialty = serializers.CharField(max_length=120, required=False, allow_blank=True)
    license_number = serializers.CharField(max_length=80, required=False, allow_blank=True, allow_null=True)

    def validate_user_id(self, value):
        """Verify that user exists in Auth Service and has doctor role"""
        user_data = get_user_info(value)

        if not user_data:
            raise serializers.ValidationError("User not found in Auth Service")

        if user_data.get('role') != 'doctor':
            raise serializers.ValidationError("User must have doctor role")

        # Check if doctor profile already exists
        if Doctor.objects.filter(user_id=value).exists():
            raise serializers.ValidationError("Doctor profile already exists for this user")

        return value

    def validate_license_number(self, value):
        """Ensure license number is unique if provided"""
        if value and Doctor.objects.filter(license_number=value).exists():
            raise serializers.ValidationError("License number already in use")
        return value

    def create(self, validated_data):
        """Create a new doctor profile"""
        return Doctor.objects.create(**validated_data)


class DoctorListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing doctors
    Includes basic user info without nested relationships
    """
    user_info = serializers.SerializerMethodField()

    class Meta:
        model = Doctor
        fields = ['user_id', 'specialty', 'license_number', 'user_info']

    def get_user_info(self, obj):
        """Fetch basic user details from Auth Service"""
        user_data = get_user_info(obj.user_id)
        if user_data:
            return {
                'name': user_data.get('name'),
                'email': user_data.get('email')
            }
        return None


class DoctorAvailabilityRequestSerializer(serializers.Serializer):
    """
    Serializer for requesting doctor availability
    Used to calculate available time slots
    """
    date = serializers.DateField(help_text="Date to check availability (YYYY-MM-DD)")
    duration_minutes = serializers.IntegerField(
        default=15,
        min_value=15,
        max_value=120,
        help_text="Appointment duration in minutes (default: 15)"
    )

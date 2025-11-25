"""
Scheduling Service Serializers
Handles serialization for appointments and notes
"""
from rest_framework import serializers
from .models import Appointment, AppointmentNote
import requests
from django.conf import settings
from datetime import datetime, timedelta


def get_doctor_info(doctor_id):
    """Fetch doctor information from Doctor Service"""
    try:
        response = requests.get(
            f"{settings.DOCTOR_SERVICE_URL}/api/doctors/{doctor_id}/",
            headers={'X-Service-Auth': settings.SERVICE_SECRET_KEY},
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error fetching doctor info: {e}")
    return None


def get_patient_info(patient_id):
    """Fetch patient information from Patient Service"""
    try:
        response = requests.get(
            f"{settings.PATIENT_SERVICE_URL}/api/patients/{patient_id}/",
            headers={'X-Service-Auth': settings.SERVICE_SECRET_KEY},
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error fetching patient info: {e}")
    return None


class AppointmentNoteSerializer(serializers.ModelSerializer):
    """Serializer for appointment notes"""
    class Meta:
        model = AppointmentNote
        fields = [
            'id', 'appointment', 'author_id', 'author_type',
            'note_text', 'is_private', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class AppointmentSerializer(serializers.ModelSerializer):
    """Serializer for appointments with cross-service data"""
    doctor_info = serializers.SerializerMethodField()
    patient_info = serializers.SerializerMethodField()
    notes = AppointmentNoteSerializer(source='appointment_notes', many=True, read_only=True)
    is_past = serializers.ReadOnlyField()
    can_be_cancelled = serializers.ReadOnlyField()

    class Meta:
        model = Appointment
        fields = [
            'id', 'doctor_id', 'patient_id', 'appointment_date',
            'start_time', 'end_time', 'duration_minutes',
            'reason', 'notes', 'status',
            'created_at', 'updated_at', 'cancelled_at', 'cancellation_reason',
            'doctor_info', 'patient_info', 'is_past', 'can_be_cancelled'
        ]
        read_only_fields = ['created_at', 'updated_at', 'cancelled_at']

    def get_doctor_info(self, obj):
        """Fetch doctor details from Doctor Service"""
        return get_doctor_info(obj.doctor_id)

    def get_patient_info(self, obj):
        """Fetch patient details from Patient Service"""
        return get_patient_info(obj.patient_id)

    def validate(self, data):
        """Validate appointment data"""
        # Check for overlapping appointments for the same doctor
        doctor_id = data.get('doctor_id')
        appointment_date = data.get('appointment_date')
        start_time = data.get('start_time')
        duration_minutes = data.get('duration_minutes', 30)

        if doctor_id and appointment_date and start_time:
            # Calculate end time
            start_datetime = datetime.combine(appointment_date, start_time)
            end_datetime = start_datetime + timedelta(minutes=duration_minutes)
            end_time = end_datetime.time()

            # Check for overlaps
            overlapping = Appointment.objects.filter(
                doctor_id=doctor_id,
                appointment_date=appointment_date,
                status__in=[Appointment.Status.SCHEDULED, Appointment.Status.CONFIRMED]
            ).exclude(pk=self.instance.pk if self.instance else None)

            for apt in overlapping:
                apt_start = datetime.combine(appointment_date, apt.start_time)
                apt_end = datetime.combine(appointment_date, apt.end_time)
                new_start = datetime.combine(appointment_date, start_time)
                new_end = datetime.combine(appointment_date, end_time)

                # Check if times overlap
                if new_start < apt_end and new_end > apt_start:
                    raise serializers.ValidationError(
                        f"Appointment overlaps with existing appointment at {apt.start_time}"
                    )

        return data


class AppointmentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing appointments"""
    doctor_name = serializers.SerializerMethodField()
    patient_name = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = [
            'id', 'doctor_id', 'patient_id', 'appointment_date',
            'start_time', 'end_time', 'status', 'reason',
            'doctor_name', 'patient_name'
        ]

    def get_doctor_name(self, obj):
        """Get doctor name from cached data if available"""
        doctor_info = get_doctor_info(obj.doctor_id)
        if doctor_info and 'user_info' in doctor_info:
            user = doctor_info['user_info']
            return f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
        return f"Doctor {obj.doctor_id}"

    def get_patient_name(self, obj):
        """Get patient name from cached data if available"""
        patient_info = get_patient_info(obj.patient_id)
        if patient_info and 'user_info' in patient_info:
            user = patient_info['user_info']
            return f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
        return f"Patient {obj.patient_id}"

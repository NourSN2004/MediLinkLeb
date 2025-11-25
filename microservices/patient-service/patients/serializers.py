"""
Patient Service Serializers
Handles serialization for patient profiles, test results, and prescriptions
"""
from rest_framework import serializers
from .models import Patient, PatientTestResult, Prescription
import requests
from django.conf import settings


def get_user_info(user_id):
    """Fetch user information from Auth Service"""
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


def get_medicine_info(medicine_id):
    """Fetch medicine information from Inventory Service"""
    try:
        response = requests.get(
            f"{settings.INVENTORY_SERVICE_URL}/api/medicines/{medicine_id}/",
            headers={'X-Service-Auth': settings.SERVICE_SECRET_KEY},
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error fetching medicine info: {e}")
    return None


class PatientSerializer(serializers.ModelSerializer):
    user_info = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = [
            'user_id', 'national_id', 'dob', 'gender', 'blood_type',
            'history_summary', 'created_at', 'updated_at', 'user_info'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_user_info(self, obj):
        """Fetch user details from Auth Service"""
        return get_user_info(obj.user_id)


class PatientTestResultSerializer(serializers.ModelSerializer):
    patient_id = serializers.IntegerField(source='patient.user_id', read_only=True)

    class Meta:
        model = PatientTestResult
        fields = [
            'id', 'patient', 'patient_id', 'test_name', 'test_date',
            'test_result', 'file_url', 'notes', 'uploaded_at'
        ]
        read_only_fields = ['uploaded_at']


class PrescriptionSerializer(serializers.ModelSerializer):
    patient_id = serializers.IntegerField(source='patient.user_id', read_only=True)
    doctor_info = serializers.SerializerMethodField()
    medicine_info = serializers.SerializerMethodField()

    class Meta:
        model = Prescription
        fields = [
            'id', 'doctor_id', 'patient', 'patient_id', 'medicine_id',
            'date_prescribed', 'dosage', 'duration', 'extra_notes',
            'status', 'created_at', 'updated_at',
            'doctor_info', 'medicine_info'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_doctor_info(self, obj):
        """Fetch doctor details from Doctor Service"""
        return get_doctor_info(obj.doctor_id)

    def get_medicine_info(self, obj):
        """Fetch medicine details from Inventory Service"""
        return get_medicine_info(obj.medicine_id)

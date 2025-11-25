"""
Pharmacy Service Serializers
Handles serialization for pharmacy profiles and staff
"""
from rest_framework import serializers
from .models import Pharmacy, PharmacistStaff
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


class PharmacySerializer(serializers.ModelSerializer):
    user_info = serializers.SerializerMethodField()
    staff_count = serializers.SerializerMethodField()

    class Meta:
        model = Pharmacy
        fields = [
            'user_id', 'address', 'license_number', 'phone',
            'created_at', 'updated_at', 'user_info', 'staff_count'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_user_info(self, obj):
        """Fetch user details from Auth Service"""
        return get_user_info(obj.user_id)

    def get_staff_count(self, obj):
        """Get count of staff members"""
        return obj.staff.count()


class PharmacistStaffSerializer(serializers.ModelSerializer):
    pharmacy_id = serializers.IntegerField(source='pharmacy.user_id', read_only=True)

    class Meta:
        model = PharmacistStaff
        fields = [
            'id', 'pharmacy', 'pharmacy_id', 'name', 'email',
            'phone', 'position', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate(self, data):
        """Validate staff email is unique within pharmacy"""
        pharmacy = data.get('pharmacy')
        email = data.get('email')

        if pharmacy and email:
            # Check if staff with this email already exists at this pharmacy
            existing = PharmacistStaff.objects.filter(
                pharmacy=pharmacy,
                email=email
            )
            # Exclude current instance if updating
            if self.instance:
                existing = existing.exclude(pk=self.instance.pk)

            if existing.exists():
                raise serializers.ValidationError({
                    'email': f'A staff member with this email already exists at this pharmacy'
                })

        return data


class PharmacyDetailSerializer(serializers.ModelSerializer):
    """Detailed pharmacy serializer including all staff"""
    user_info = serializers.SerializerMethodField()
    staff = PharmacistStaffSerializer(many=True, read_only=True)
    staff_count = serializers.SerializerMethodField()

    class Meta:
        model = Pharmacy
        fields = [
            'user_id', 'address', 'license_number', 'phone',
            'created_at', 'updated_at', 'user_info',
            'staff', 'staff_count'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_user_info(self, obj):
        """Fetch user details from Auth Service"""
        return get_user_info(obj.user_id)

    def get_staff_count(self, obj):
        """Get count of staff members"""
        return obj.staff.count()

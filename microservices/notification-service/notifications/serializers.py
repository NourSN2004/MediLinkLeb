"""
Notification Service Serializers
Handles serialization for notifications
"""
from rest_framework import serializers
from .models import Notification, NotificationPreference
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


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for notifications"""
    user_info = serializers.SerializerMethodField()
    is_scheduled = serializers.ReadOnlyField()

    class Meta:
        model = Notification
        fields = [
            'id', 'user_id', 'notification_type', 'title', 'message',
            'appointment_id', 'prescription_id', 'pharmacy_id', 'medicine_id',
            'is_read', 'read_at', 'priority',
            'send_email', 'email_sent', 'email_sent_at',
            'send_sms', 'sms_sent', 'sms_sent_at',
            'scheduled_for', 'sent_at', 'created_at', 'updated_at',
            'user_info', 'is_scheduled'
        ]
        read_only_fields = [
            'email_sent', 'email_sent_at', 'sms_sent', 'sms_sent_at',
            'sent_at', 'read_at', 'created_at', 'updated_at'
        ]

    def get_user_info(self, obj):
        """Fetch user details from Auth Service"""
        return get_user_info(obj.user_id)


class NotificationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing notifications"""
    class Meta:
        model = Notification
        fields = [
            'id', 'user_id', 'notification_type', 'title',
            'is_read', 'priority', 'created_at'
        ]


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for notification preferences"""
    class Meta:
        model = NotificationPreference
        fields = [
            'id', 'user_id',
            'email_enabled', 'email_appointments', 'email_prescriptions', 'email_marketing',
            'sms_enabled', 'sms_appointments', 'sms_prescriptions',
            'in_app_enabled',
            'quiet_hours_enabled', 'quiet_hours_start', 'quiet_hours_end',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

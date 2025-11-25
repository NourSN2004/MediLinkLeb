"""
Notification Service Models
Handles user notifications and alerts
"""
from django.db import models
from django.core.exceptions import ValidationError


class Notification(models.Model):
    """
    Notification model for sending alerts to users
    Note: user_id references User in Auth Service (cross-service)
    """
    # Cross-service reference
    user_id = models.IntegerField(help_text="Reference to user in Auth Service")

    # Notification details
    class NotificationType(models.TextChoices):
        APPOINTMENT_REMINDER = 'appointment_reminder', 'Appointment Reminder'
        APPOINTMENT_CANCELLED = 'appointment_cancelled', 'Appointment Cancelled'
        PRESCRIPTION_READY = 'prescription_ready', 'Prescription Ready'
        LOW_STOCK_ALERT = 'low_stock', 'Low Stock Alert'
        EXPIRY_WARNING = 'expiry_warning', 'Expiry Warning'
        GENERAL = 'general', 'General'

    notification_type = models.CharField(
        max_length=50,
        choices=NotificationType.choices,
        default=NotificationType.GENERAL
    )

    title = models.CharField(max_length=200, help_text="Notification title")
    message = models.TextField(help_text="Notification message")

    # Optional references to related entities
    appointment_id = models.IntegerField(null=True, blank=True)
    prescription_id = models.IntegerField(null=True, blank=True)
    pharmacy_id = models.IntegerField(null=True, blank=True)
    medicine_id = models.IntegerField(null=True, blank=True)

    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    # Priority
    class Priority(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'
        URGENT = 'urgent', 'Urgent'

    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM
    )

    # Delivery options
    send_email = models.BooleanField(default=False, help_text="Send email notification")
    email_sent = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)

    send_sms = models.BooleanField(default=False, help_text="Send SMS notification")
    sms_sent = models.BooleanField(default=False)
    sms_sent_at = models.DateTimeField(null=True, blank=True)

    # Scheduling
    scheduled_for = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Schedule notification for future delivery"
    )
    sent_at = models.DateTimeField(null=True, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_id', 'is_read']),
            models.Index(fields=['notification_type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['scheduled_for']),
        ]

    def __str__(self):
        return f"Notification for User {self.user_id}: {self.title}"

    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            from django.utils import timezone
            self.is_read = True
            self.read_at = timezone.now()
            self.save()

    def is_scheduled(self):
        """Check if notification is scheduled for future"""
        if self.scheduled_for:
            from django.utils import timezone
            return self.scheduled_for > timezone.now()
        return False


class NotificationPreference(models.Model):
    """
    User preferences for notifications
    Note: user_id references User in Auth Service (cross-service)
    """
    user_id = models.IntegerField(unique=True, help_text="Reference to user in Auth Service")

    # Email preferences
    email_enabled = models.BooleanField(default=True)
    email_appointments = models.BooleanField(default=True)
    email_prescriptions = models.BooleanField(default=True)
    email_marketing = models.BooleanField(default=False)

    # SMS preferences
    sms_enabled = models.BooleanField(default=False)
    sms_appointments = models.BooleanField(default=False)
    sms_prescriptions = models.BooleanField(default=False)

    # In-app notification preferences
    in_app_enabled = models.BooleanField(default=True)

    # Quiet hours
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'notification_preferences'
        indexes = [
            models.Index(fields=['user_id']),
        ]

    def __str__(self):
        return f"Notification Preferences for User {self.user_id}"

"""
Notification Service Admin Interface
Django admin configuration for notifications
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Notification, NotificationPreference


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin interface for Notification model"""
    list_display = [
        'id', 'user_id', 'title', 'notification_type', 'priority_badge',
        'is_read', 'created_at'
    ]
    list_filter = ['notification_type', 'priority', 'is_read', 'created_at']
    search_fields = ['user_id', 'title', 'message']
    readonly_fields = [
        'created_at', 'updated_at', 'read_at', 'email_sent_at',
        'sms_sent_at', 'sent_at', 'is_scheduled'
    ]
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Recipient', {
            'fields': ('user_id',)
        }),
        ('Notification Details', {
            'fields': ('notification_type', 'title', 'message', 'priority')
        }),
        ('References', {
            'fields': ('appointment_id', 'prescription_id', 'pharmacy_id', 'medicine_id')
        }),
        ('Read Status', {
            'fields': ('is_read', 'read_at')
        }),
        ('Delivery Options', {
            'fields': (
                'send_email', 'email_sent', 'email_sent_at',
                'send_sms', 'sms_sent', 'sms_sent_at'
            )
        }),
        ('Scheduling', {
            'fields': ('scheduled_for', 'sent_at', 'is_scheduled')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_as_read', 'mark_as_unread']

    def priority_badge(self, obj):
        """Display colored badge for priority"""
        colors = {
            'low': '#6b7280',
            'medium': '#3b82f6',
            'high': '#f59e0b',
            'urgent': '#ef4444',
        }
        color = colors.get(obj.priority, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_priority_display()
        )
    priority_badge.short_description = 'Priority'

    def mark_as_read(self, request, queryset):
        """Mark selected notifications as read"""
        from django.utils import timezone
        count = queryset.update(is_read=True, read_at=timezone.now())
        self.message_user(request, f'{count} notification(s) marked as read.')
    mark_as_read.short_description = 'Mark selected as read'

    def mark_as_unread(self, request, queryset):
        """Mark selected notifications as unread"""
        count = queryset.update(is_read=False, read_at=None)
        self.message_user(request, f'{count} notification(s) marked as unread.')
    mark_as_unread.short_description = 'Mark selected as unread'


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    """Admin interface for NotificationPreference model"""
    list_display = [
        'user_id', 'email_enabled', 'sms_enabled', 'in_app_enabled',
        'quiet_hours_enabled', 'created_at'
    ]
    list_filter = ['email_enabled', 'sms_enabled', 'in_app_enabled', 'quiet_hours_enabled']
    search_fields = ['user_id']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('User', {
            'fields': ('user_id',)
        }),
        ('Email Preferences', {
            'fields': ('email_enabled', 'email_appointments', 'email_prescriptions', 'email_marketing')
        }),
        ('SMS Preferences', {
            'fields': ('sms_enabled', 'sms_appointments', 'sms_prescriptions')
        }),
        ('In-App Preferences', {
            'fields': ('in_app_enabled',)
        }),
        ('Quiet Hours', {
            'fields': ('quiet_hours_enabled', 'quiet_hours_start', 'quiet_hours_end')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

"""
Scheduling Service Admin Interface
Django admin configuration for appointments and notes
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Appointment, AppointmentNote


class AppointmentNoteInline(admin.TabularInline):
    """Inline admin for appointment notes"""
    model = AppointmentNote
    extra = 0
    fields = ['author_id', 'author_type', 'note_text', 'is_private', 'created_at']
    readonly_fields = ['created_at']


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    """Admin interface for Appointment model"""
    list_display = [
        'id', 'doctor_id', 'patient_id', 'appointment_date',
        'start_time', 'end_time', 'status_badge', 'created_at'
    ]
    list_filter = ['status', 'appointment_date', 'created_at']
    search_fields = ['doctor_id', 'patient_id', 'reason']
    readonly_fields = ['created_at', 'updated_at', 'cancelled_at', 'is_past', 'can_be_cancelled']
    date_hierarchy = 'appointment_date'
    inlines = [AppointmentNoteInline]

    fieldsets = (
        ('Appointment Details', {
            'fields': ('doctor_id', 'patient_id', 'appointment_date', 'start_time', 'end_time', 'duration_minutes')
        }),
        ('Information', {
            'fields': ('reason', 'notes')
        }),
        ('Status', {
            'fields': ('status', 'cancellation_reason', 'cancelled_at')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'is_past', 'can_be_cancelled'),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_confirmed', 'mark_completed', 'mark_cancelled', 'mark_no_show']

    def status_badge(self, obj):
        """Display colored status badge"""
        colors = {
            'scheduled': '#3b82f6',
            'confirmed': '#10b981',
            'in_progress': '#f59e0b',
            'completed': '#6b7280',
            'cancelled': '#ef4444',
            'no_show': '#ef4444',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def mark_confirmed(self, request, queryset):
        """Mark selected appointments as confirmed"""
        count = queryset.filter(status=Appointment.Status.SCHEDULED).update(status=Appointment.Status.CONFIRMED)
        self.message_user(request, f'{count} appointment(s) marked as confirmed.')
    mark_confirmed.short_description = 'Mark selected as confirmed'

    def mark_completed(self, request, queryset):
        """Mark selected appointments as completed"""
        count = queryset.update(status=Appointment.Status.COMPLETED)
        self.message_user(request, f'{count} appointment(s) marked as completed.')
    mark_completed.short_description = 'Mark selected as completed'

    def mark_cancelled(self, request, queryset):
        """Mark selected appointments as cancelled"""
        from datetime import datetime
        count = queryset.update(status=Appointment.Status.CANCELLED, cancelled_at=datetime.now())
        self.message_user(request, f'{count} appointment(s) marked as cancelled.')
    mark_cancelled.short_description = 'Mark selected as cancelled'

    def mark_no_show(self, request, queryset):
        """Mark selected appointments as no show"""
        count = queryset.update(status=Appointment.Status.NO_SHOW)
        self.message_user(request, f'{count} appointment(s) marked as no show.')
    mark_no_show.short_description = 'Mark selected as no show'


@admin.register(AppointmentNote)
class AppointmentNoteAdmin(admin.ModelAdmin):
    """Admin interface for AppointmentNote model"""
    list_display = ['id', 'appointment', 'author_id', 'author_type', 'is_private', 'created_at']
    list_filter = ['author_type', 'is_private', 'created_at']
    search_fields = ['note_text', 'author_id', 'appointment__id']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Note Details', {
            'fields': ('appointment', 'author_id', 'author_type')
        }),
        ('Content', {
            'fields': ('note_text', 'is_private')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Optimize queries"""
        qs = super().get_queryset(request)
        return qs.select_related('appointment')

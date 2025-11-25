"""
Doctor Service Admin Configuration
"""
from django.contrib import admin
from .models import Doctor, DoctorWorkingHours, DoctorTimeOff


class DoctorWorkingHoursInline(admin.TabularInline):
    """Inline admin for doctor working hours"""
    model = DoctorWorkingHours
    extra = 1
    fields = ['day_of_week', 'start_time', 'end_time']


class DoctorTimeOffInline(admin.TabularInline):
    """Inline admin for doctor time-off"""
    model = DoctorTimeOff
    extra = 0
    fields = ['date', 'start_time', 'end_time', 'reason']
    ordering = ['-date']


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    """Admin for Doctor model"""
    list_display = ['user_id', 'specialty', 'license_number', 'created_at']
    list_filter = ['specialty', 'created_at']
    search_fields = ['user_id', 'specialty', 'license_number']
    readonly_fields = ['user_id', 'created_at', 'updated_at']
    inlines = [DoctorWorkingHoursInline, DoctorTimeOffInline]

    fieldsets = (
        ('Doctor Information', {
            'fields': ('user_id', 'specialty', 'license_number')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DoctorWorkingHours)
class DoctorWorkingHoursAdmin(admin.ModelAdmin):
    """Admin for DoctorWorkingHours model"""
    list_display = ['doctor', 'day_of_week', 'start_time', 'end_time']
    list_filter = ['day_of_week']
    search_fields = ['doctor__user_id']


@admin.register(DoctorTimeOff)
class DoctorTimeOffAdmin(admin.ModelAdmin):
    """Admin for DoctorTimeOff model"""
    list_display = ['doctor', 'date', 'start_time', 'end_time', 'reason']
    list_filter = ['date']
    search_fields = ['doctor__user_id', 'reason']
    date_hierarchy = 'date'

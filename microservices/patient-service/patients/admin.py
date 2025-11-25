"""
Patient Service Admin Interface
Django admin configuration for patients, test results, and prescriptions
"""
from django.contrib import admin
from .models import Patient, PatientTestResult, Prescription


class PatientTestResultInline(admin.TabularInline):
    """Inline admin for patient test results"""
    model = PatientTestResult
    extra = 0
    fields = ['test_name', 'test_date', 'test_result', 'file_url']
    readonly_fields = ['uploaded_at']


class PrescriptionInline(admin.TabularInline):
    """Inline admin for patient prescriptions"""
    model = Prescription
    extra = 0
    fields = ['doctor_id', 'medicine_id', 'date_prescribed', 'dosage', 'duration', 'status']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    """Admin interface for Patient model"""
    list_display = [
        'user_id', 'national_id', 'gender', 'blood_type',
        'dob', 'test_results_count', 'prescriptions_count', 'created_at'
    ]
    list_filter = ['gender', 'blood_type', 'created_at']
    search_fields = ['user_id', 'national_id']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [PatientTestResultInline, PrescriptionInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('user_id', 'national_id', 'dob', 'gender', 'blood_type')
        }),
        ('Medical History', {
            'fields': ('history_summary',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def test_results_count(self, obj):
        """Display count of test results"""
        return obj.test_results.count()
    test_results_count.short_description = 'Test Results'

    def prescriptions_count(self, obj):
        """Display count of prescriptions"""
        return obj.prescriptions.count()
    prescriptions_count.short_description = 'Prescriptions'


@admin.register(PatientTestResult)
class PatientTestResultAdmin(admin.ModelAdmin):
    """Admin interface for PatientTestResult model"""
    list_display = [
        'id', 'patient', 'test_name', 'test_date', 'has_file', 'uploaded_at'
    ]
    list_filter = ['test_date', 'uploaded_at']
    search_fields = ['test_name', 'patient__user_id', 'patient__national_id']
    readonly_fields = ['uploaded_at']
    date_hierarchy = 'test_date'

    fieldsets = (
        ('Test Information', {
            'fields': ('patient', 'test_name', 'test_date')
        }),
        ('Results', {
            'fields': ('test_result', 'file_url', 'notes')
        }),
        ('Metadata', {
            'fields': ('uploaded_at',),
            'classes': ('collapse',)
        }),
    )

    def has_file(self, obj):
        """Indicate if test result has a file"""
        return bool(obj.file_url)
    has_file.boolean = True
    has_file.short_description = 'Has File'

    def get_queryset(self, request):
        """Optimize queries"""
        qs = super().get_queryset(request)
        return qs.select_related('patient')


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    """Admin interface for Prescription model"""
    list_display = [
        'id', 'patient', 'doctor_id', 'medicine_id',
        'date_prescribed', 'status', 'created_at'
    ]
    list_filter = ['status', 'date_prescribed', 'created_at']
    search_fields = [
        'patient__user_id', 'patient__national_id',
        'doctor_id', 'medicine_id'
    ]
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date_prescribed'

    fieldsets = (
        ('Prescription Details', {
            'fields': ('patient', 'doctor_id', 'medicine_id', 'date_prescribed')
        }),
        ('Dosage Information', {
            'fields': ('dosage', 'duration', 'extra_notes')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_completed', 'mark_cancelled', 'mark_active']

    def mark_completed(self, request, queryset):
        """Mark selected prescriptions as completed"""
        count = queryset.update(status=Prescription.Status.COMPLETED)
        self.message_user(request, f'{count} prescription(s) marked as completed.')
    mark_completed.short_description = 'Mark selected as completed'

    def mark_cancelled(self, request, queryset):
        """Mark selected prescriptions as cancelled"""
        count = queryset.update(status=Prescription.Status.CANCELLED)
        self.message_user(request, f'{count} prescription(s) marked as cancelled.')
    mark_cancelled.short_description = 'Mark selected as cancelled'

    def mark_active(self, request, queryset):
        """Mark selected prescriptions as active"""
        count = queryset.update(status=Prescription.Status.ACTIVE)
        self.message_user(request, f'{count} prescription(s) marked as active.')
    mark_active.short_description = 'Mark selected as active'

    def get_queryset(self, request):
        """Optimize queries"""
        qs = super().get_queryset(request)
        return qs.select_related('patient')

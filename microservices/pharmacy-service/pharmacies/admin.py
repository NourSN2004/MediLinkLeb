"""
Pharmacy Service Django Admin Configuration
"""
from django.contrib import admin
from .models import Pharmacy, PharmacistStaff


class PharmacistStaffInline(admin.TabularInline):
    """Inline admin for pharmacist staff"""
    model = PharmacistStaff
    extra = 1
    fields = ['name', 'email', 'phone', 'position']


@admin.register(Pharmacy)
class PharmacyAdmin(admin.ModelAdmin):
    """Admin interface for Pharmacy model"""
    list_display = ['user_id', 'address', 'license_number', 'phone', 'staff_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user_id', 'address', 'license_number']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [PharmacistStaffInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('user_id', 'license_number')
        }),
        ('Contact Information', {
            'fields': ('address', 'phone')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def staff_count(self, obj):
        """Display number of staff members"""
        return obj.staff.count()
    staff_count.short_description = 'Staff Count'


@admin.register(PharmacistStaff)
class PharmacistStaffAdmin(admin.ModelAdmin):
    """Admin interface for PharmacistStaff model"""
    list_display = ['name', 'pharmacy', 'email', 'phone', 'position', 'created_at']
    list_filter = ['pharmacy', 'position', 'created_at']
    search_fields = ['name', 'email', 'pharmacy__user_id']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Staff Information', {
            'fields': ('pharmacy', 'name', 'position')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('pharmacy')

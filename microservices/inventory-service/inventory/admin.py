"""
Inventory Service Admin Interface
Django admin configuration for medicines and stock
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Medicine, PharmacyStock, StockTransaction


class PharmacyStockInline(admin.TabularInline):
    """Inline admin for pharmacy stock"""
    model = PharmacyStock
    extra = 0
    fields = ['pharmacy_id', 'quantity', 'reorder_level', 'expiry_date', 'selling_price']
    readonly_fields = ['created_at']


class StockTransactionInline(admin.TabularInline):
    """Inline admin for stock transactions"""
    model = StockTransaction
    extra = 0
    fields = ['transaction_type', 'quantity_change', 'quantity_after', 'notes', 'transaction_date']
    readonly_fields = ['transaction_date', 'quantity_before', 'quantity_after']


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    """Admin interface for Medicine model"""
    list_display = [
        'name', 'generic_name', 'strength', 'form',
        'category', 'requires_prescription_badge', 'base_price', 'is_active'
    ]
    list_filter = ['category', 'form', 'requires_prescription', 'is_active', 'created_at']
    search_fields = ['name', 'generic_name', 'manufacturer']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [PharmacyStockInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'generic_name', 'manufacturer')
        }),
        ('Medicine Details', {
            'fields': ('form', 'strength', 'description', 'category')
        }),
        ('Prescription & Pricing', {
            'fields': ('requires_prescription', 'base_price')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_active', 'mark_inactive']

    def requires_prescription_badge(self, obj):
        """Display colored badge for prescription requirement"""
        if obj.requires_prescription:
            return format_html(
                '<span style="background-color: #ef4444; color: white; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: bold;">Rx Required</span>'
            )
        return format_html(
            '<span style="background-color: #10b981; color: white; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: bold;">OTC</span>'
        )
    requires_prescription_badge.short_description = 'Prescription'

    def mark_active(self, request, queryset):
        """Mark selected medicines as active"""
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} medicine(s) marked as active.')
    mark_active.short_description = 'Mark selected as active'

    def mark_inactive(self, request, queryset):
        """Mark selected medicines as inactive"""
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} medicine(s) marked as inactive.')
    mark_inactive.short_description = 'Mark selected as inactive'


@admin.register(PharmacyStock)
class PharmacyStockAdmin(admin.ModelAdmin):
    """Admin interface for PharmacyStock model"""
    list_display = [
        'pharmacy_id', 'medicine', 'quantity', 'stock_status',
        'expiry_date', 'expiry_status', 'selling_price', 'batch_number'
    ]
    list_filter = ['pharmacy_id', 'expiry_date', 'created_at']
    search_fields = ['medicine__name', 'batch_number', 'pharmacy_id']
    readonly_fields = ['created_at', 'updated_at', 'is_low_stock', 'is_expiring_soon', 'is_expired', 'days_until_expiry']
    date_hierarchy = 'expiry_date'
    inlines = [StockTransactionInline]

    fieldsets = (
        ('Stock Information', {
            'fields': ('pharmacy_id', 'medicine', 'quantity', 'reorder_level', 'max_stock_level')
        }),
        ('Batch Information', {
            'fields': ('batch_number', 'expiry_date', 'manufacturing_date')
        }),
        ('Pricing & Location', {
            'fields': ('selling_price', 'shelf_location')
        }),
        ('Status', {
            'fields': ('is_low_stock', 'is_expiring_soon', 'is_expired', 'days_until_expiry'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('last_restocked_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def stock_status(self, obj):
        """Display colored badge for stock status"""
        if obj.is_low_stock():
            return format_html(
                '<span style="background-color: #ef4444; color: white; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: bold;">Low Stock</span>'
            )
        return format_html(
            '<span style="background-color: #10b981; color: white; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: bold;">In Stock</span>'
        )
    stock_status.short_description = 'Stock Status'

    def expiry_status(self, obj):
        """Display colored badge for expiry status"""
        if obj.is_expired():
            return format_html(
                '<span style="background-color: #991b1b; color: white; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: bold;">Expired</span>'
            )
        elif obj.is_expiring_soon():
            return format_html(
                '<span style="background-color: #f59e0b; color: white; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: bold;">Expiring Soon</span>'
            )
        return format_html(
            '<span style="background-color: #10b981; color: white; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: bold;">Valid</span>'
        )
    expiry_status.short_description = 'Expiry Status'

    def get_queryset(self, request):
        """Optimize queries"""
        qs = super().get_queryset(request)
        return qs.select_related('medicine')


@admin.register(StockTransaction)
class StockTransactionAdmin(admin.ModelAdmin):
    """Admin interface for StockTransaction model"""
    list_display = [
        'id', 'pharmacy_stock', 'transaction_type', 'quantity_change',
        'quantity_before', 'quantity_after', 'transaction_date'
    ]
    list_filter = ['transaction_type', 'transaction_date']
    search_fields = ['pharmacy_stock__medicine__name', 'notes']
    readonly_fields = ['transaction_date']
    date_hierarchy = 'transaction_date'

    fieldsets = (
        ('Transaction Details', {
            'fields': ('pharmacy_stock', 'transaction_type')
        }),
        ('Quantity Changes', {
            'fields': ('quantity_change', 'quantity_before', 'quantity_after')
        }),
        ('References', {
            'fields': ('prescription_id', 'user_id', 'notes')
        }),
        ('Metadata', {
            'fields': ('transaction_date',),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Optimize queries"""
        qs = super().get_queryset(request)
        return qs.select_related('pharmacy_stock__medicine')

    def has_add_permission(self, request):
        """Transactions should be created via API, not admin"""
        return False

    def has_change_permission(self, request, obj=None):
        """Transactions should not be edited"""
        return False

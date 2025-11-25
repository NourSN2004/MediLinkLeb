"""
Inventory Service Models
Handles medicine catalog and pharmacy stock management
"""
from django.db import models
from django.core.exceptions import ValidationError
from datetime import date, timedelta


class Medicine(models.Model):
    """
    Medicine catalog - master list of all medicines
    """
    name = models.CharField(max_length=200, help_text="Medicine name")
    generic_name = models.CharField(max_length=200, blank=True, help_text="Generic/scientific name")
    manufacturer = models.CharField(max_length=200, blank=True)

    # Medicine details
    form = models.CharField(
        max_length=50,
        help_text="Form (tablet, capsule, syrup, injection, etc.)"
    )
    strength = models.CharField(max_length=100, help_text="Strength (e.g., 500mg, 10ml)")
    description = models.TextField(blank=True)

    # Classification
    category = models.CharField(max_length=100, blank=True, help_text="Medicine category")
    requires_prescription = models.BooleanField(default=True)

    # Pricing
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Base/recommended price"
    )

    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'medicines'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['generic_name']),
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return f"{self.name} ({self.strength})"


class PharmacyStock(models.Model):
    """
    Stock levels for each medicine at each pharmacy
    Note: pharmacy_id references Pharmacy Service (cross-service)
    """
    # Cross-service reference
    pharmacy_id = models.IntegerField(help_text="Reference to pharmacy in Pharmacy Service")

    medicine = models.ForeignKey(
        Medicine,
        on_delete=models.CASCADE,
        related_name="stock_levels"
    )

    # Stock information
    quantity = models.IntegerField(default=0, help_text="Current quantity in stock")
    reorder_level = models.IntegerField(default=10, help_text="Minimum level before reorder")
    max_stock_level = models.IntegerField(default=100, help_text="Maximum stock level")

    # Batch information
    batch_number = models.CharField(max_length=100, blank=True)
    expiry_date = models.DateField(help_text="Expiry date of this batch")
    manufacturing_date = models.DateField(null=True, blank=True)

    # Pricing (can differ from base price)
    selling_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Selling price at this pharmacy"
    )

    # Location
    shelf_location = models.CharField(max_length=100, blank=True, help_text="Physical location in pharmacy")

    # Metadata
    last_restocked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pharmacy_stock'
        ordering = ['pharmacy_id', 'medicine__name']
        indexes = [
            models.Index(fields=['pharmacy_id', 'medicine']),
            models.Index(fields=['expiry_date']),
            models.Index(fields=['quantity']),
        ]
        unique_together = [['pharmacy_id', 'medicine', 'batch_number']]

    def __str__(self):
        return f"Pharmacy {self.pharmacy_id} - {self.medicine.name} (Qty: {self.quantity})"

    def is_low_stock(self):
        """Check if stock is below reorder level"""
        return self.quantity <= self.reorder_level

    def is_expiring_soon(self, days=30):
        """Check if medicine is expiring within specified days"""
        if self.expiry_date:
            return (self.expiry_date - date.today()).days <= days
        return False

    def is_expired(self):
        """Check if medicine has expired"""
        return self.expiry_date < date.today()

    def days_until_expiry(self):
        """Calculate days until expiry"""
        if self.expiry_date:
            return (self.expiry_date - date.today()).days
        return None

    def clean(self):
        """Validate stock data"""
        super().clean()

        if self.quantity < 0:
            raise ValidationError('Quantity cannot be negative')

        if self.reorder_level < 0:
            raise ValidationError('Reorder level cannot be negative')

        if self.expiry_date and self.expiry_date < date.today():
            raise ValidationError('Cannot add expired medicine to stock')


class StockTransaction(models.Model):
    """
    Track all stock movements (additions, sales, adjustments)
    """
    pharmacy_stock = models.ForeignKey(
        PharmacyStock,
        on_delete=models.CASCADE,
        related_name="transactions"
    )

    # Transaction details
    class TransactionType(models.TextChoices):
        PURCHASE = 'purchase', 'Purchase/Restock'
        SALE = 'sale', 'Sale'
        ADJUSTMENT = 'adjustment', 'Adjustment'
        RETURN = 'return', 'Return'
        EXPIRED = 'expired', 'Expired/Disposed'

    transaction_type = models.CharField(
        max_length=20,
        choices=TransactionType.choices
    )

    quantity_change = models.IntegerField(help_text="Change in quantity (positive or negative)")
    quantity_before = models.IntegerField(help_text="Quantity before transaction")
    quantity_after = models.IntegerField(help_text="Quantity after transaction")

    # Optional references
    prescription_id = models.IntegerField(null=True, blank=True, help_text="Related prescription ID if applicable")
    user_id = models.IntegerField(null=True, blank=True, help_text="User who made the transaction")

    # Notes
    notes = models.TextField(blank=True)

    # Metadata
    transaction_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'stock_transactions'
        ordering = ['-transaction_date']
        indexes = [
            models.Index(fields=['pharmacy_stock', 'transaction_date']),
            models.Index(fields=['transaction_type']),
        ]

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.pharmacy_stock.medicine.name} ({self.quantity_change:+d})"

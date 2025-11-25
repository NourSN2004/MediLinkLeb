"""
Pharmacy Service Models
Handles pharmacy profiles and pharmacist staff management
"""
from django.db import models
from django.core.exceptions import ValidationError


class Pharmacy(models.Model):
    """
    Pharmacy profile extending user from Auth service
    Note: user_id references User in Auth Service (cross-service reference)
    """
    # Reference to User in Auth Service (not a ForeignKey for microservices)
    user_id = models.IntegerField(unique=True, primary_key=True)

    address = models.CharField(max_length=255, blank=True, help_text="Pharmacy physical address")
    license_number = models.CharField(
        max_length=80,
        unique=True,
        blank=True,
        null=True,
        help_text="Pharmacy license/registration number"
    )
    phone = models.CharField(max_length=30, blank=True, help_text="Contact phone number")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pharmacies'
        verbose_name = 'Pharmacy'
        verbose_name_plural = 'Pharmacies'
        indexes = [
            models.Index(fields=['user_id']),
            models.Index(fields=['license_number']),
        ]

    def __str__(self):
        return f"Pharmacy {self.user_id}"


class PharmacistStaff(models.Model):
    """
    Pharmacist staff members working at a pharmacy
    """
    pharmacy = models.ForeignKey(
        Pharmacy,
        on_delete=models.CASCADE,
        related_name="staff",
        help_text="Pharmacy this staff member works at"
    )
    name = models.CharField(max_length=120, help_text="Staff member full name")
    email = models.EmailField(help_text="Staff member email")
    phone = models.CharField(max_length=30, blank=True, help_text="Staff member phone number")
    position = models.CharField(
        max_length=100,
        blank=True,
        help_text="Job title/position (e.g., Pharmacist, Assistant, Manager)"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pharmacist_staff'
        verbose_name = 'Pharmacist Staff'
        verbose_name_plural = 'Pharmacist Staff'
        unique_together = ('pharmacy', 'email')
        ordering = ['name']
        indexes = [
            models.Index(fields=['pharmacy', 'email']),
        ]

    def __str__(self):
        return f"{self.name} - {self.pharmacy}"

    def clean(self):
        """Validate email is unique within pharmacy"""
        if self.email:
            existing = PharmacistStaff.objects.filter(
                pharmacy=self.pharmacy,
                email=self.email
            ).exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError(f"A staff member with email {self.email} already exists at this pharmacy")

"""
User model for Auth & Access Service
"""
from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    Custom User model with role-based authentication.
    Extends Django's AbstractUser to add role, phone, and password reset fields.
    """

    class Role(models.TextChoices):
        DOCTOR = "doctor", "Doctor"
        PATIENT = "patient", "Patient"
        PHARMACY = "pharmacy", "Pharmacy"

    email = models.EmailField(unique=True, db_index=True)
    name = models.CharField(max_length=120)
    role = models.CharField(max_length=20, choices=Role.choices, db_index=True)
    phone_number = models.CharField(max_length=30, blank=True)

    # Password reset fields
    reset_password_token = models.CharField(max_length=100, blank=True, null=True)
    reset_password_expires = models.DateTimeField(null=True, blank=True)

    # Email verification (for future use)
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'name']

    class Meta:
        db_table = 'auth_users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
        ]

    def __str__(self):
        return f"{self.name} ({self.role})"

    @property
    def is_doctor(self):
        return self.role == self.Role.DOCTOR

    @property
    def is_patient(self):
        return self.role == self.Role.PATIENT

    @property
    def is_pharmacy(self):
        return self.role == self.Role.PHARMACY

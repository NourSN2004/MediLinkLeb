"""
Patient Service Models
Handles patient profiles, medical history, test results, and prescriptions
"""
from django.db import models
from django.core.exceptions import ValidationError


class Patient(models.Model):
    """
    Patient profile extending user from Auth service
    Note: user_id references User in Auth Service (cross-service reference)
    """
    # Reference to User in Auth Service (not a ForeignKey for microservices)
    user_id = models.IntegerField(unique=True, primary_key=True)

    national_id = models.CharField(max_length=40, blank=True)
    dob = models.DateField(null=True, blank=True, help_text="Date of birth")
    gender = models.CharField(max_length=20, blank=True, choices=[
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ])
    blood_type = models.CharField(max_length=5, blank=True, choices=[
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    ])
    history_summary = models.TextField(blank=True, help_text="Medical history summary")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'patients'
        indexes = [
            models.Index(fields=['user_id']),
            models.Index(fields=['national_id']),
        ]

    def __str__(self):
        return f"Patient {self.user_id}"


class PatientTestResult(models.Model):
    """
    Patient's test results (uploaded files)
    """
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="test_results"
    )
    test_name = models.CharField(max_length=200, help_text="Name of the test")
    test_date = models.DateField(help_text="Date the test was performed")
    test_result = models.TextField(blank=True, help_text="Test result details")
    file_url = models.URLField(blank=True, help_text="URL to uploaded file (if any)")
    notes = models.TextField(blank=True)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'patient_test_results'
        ordering = ['-test_date', '-uploaded_at']
        indexes = [
            models.Index(fields=['patient', 'test_date']),
        ]

    def __str__(self):
        return f"Test Result for Patient {self.patient.user_id} - {self.test_name}"


class Prescription(models.Model):
    """
    Prescriptions written for patients
    Note: doctor_id and medicine_id are cross-service references
    """
    # Cross-service references
    doctor_id = models.IntegerField(help_text="Reference to doctor in Doctor Service")
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="prescriptions"
    )
    medicine_id = models.IntegerField(help_text="Reference to medicine in Inventory Service")

    date_prescribed = models.DateField()
    dosage = models.CharField(max_length=120, help_text="Dosage instructions")
    duration = models.CharField(max_length=120, help_text="Duration of treatment")
    extra_notes = models.TextField(blank=True)

    # Status tracking
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'prescriptions'
        ordering = ['-date_prescribed']
        indexes = [
            models.Index(fields=['patient', 'date_prescribed']),
            models.Index(fields=['doctor_id']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Prescription for Patient {self.patient.user_id} by Doctor {self.doctor_id}"

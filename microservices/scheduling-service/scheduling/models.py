"""
Scheduling Service Models
Handles appointments between patients and doctors
"""
from django.db import models
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta


class Appointment(models.Model):
    """
    Appointment model for doctor-patient scheduling
    Note: doctor_id and patient_id reference other services (cross-service)
    """
    # Cross-service references
    doctor_id = models.IntegerField(help_text="Reference to doctor in Doctor Service")
    patient_id = models.IntegerField(help_text="Reference to patient in Patient Service")

    # Appointment timing
    appointment_date = models.DateField(help_text="Date of appointment")
    start_time = models.TimeField(help_text="Start time of appointment")
    end_time = models.TimeField(help_text="End time of appointment")
    duration_minutes = models.IntegerField(default=30, help_text="Duration in minutes")

    # Appointment details
    reason = models.TextField(blank=True, help_text="Reason for visit")
    notes = models.TextField(blank=True, help_text="Additional notes")

    # Status tracking
    class Status(models.TextChoices):
        SCHEDULED = 'scheduled', 'Scheduled'
        CONFIRMED = 'confirmed', 'Confirmed'
        IN_PROGRESS = 'in_progress', 'In Progress'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'
        NO_SHOW = 'no_show', 'No Show'

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)

    class Meta:
        db_table = 'appointments'
        ordering = ['appointment_date', 'start_time']
        indexes = [
            models.Index(fields=['doctor_id', 'appointment_date']),
            models.Index(fields=['patient_id', 'appointment_date']),
            models.Index(fields=['status']),
            models.Index(fields=['appointment_date', 'start_time']),
        ]
        # Ensure no double booking for same doctor at same time
        unique_together = [['doctor_id', 'appointment_date', 'start_time']]

    def __str__(self):
        return f"Appointment: Doctor {self.doctor_id} - Patient {self.patient_id} on {self.appointment_date} at {self.start_time}"

    def clean(self):
        """Validate appointment times"""
        super().clean()

        # Validate end_time is after start_time
        if self.start_time and self.end_time:
            if self.end_time <= self.start_time:
                raise ValidationError('End time must be after start time.')

        # Validate appointment is not in the past (for new appointments)
        if not self.pk and self.appointment_date and self.start_time:
            appointment_datetime = datetime.combine(self.appointment_date, self.start_time)
            if appointment_datetime < datetime.now():
                raise ValidationError('Cannot create appointment in the past.')

    def save(self, *args, **kwargs):
        # Calculate end_time based on start_time and duration if not set
        if self.start_time and not self.end_time:
            start_datetime = datetime.combine(self.appointment_date, self.start_time)
            end_datetime = start_datetime + timedelta(minutes=self.duration_minutes)
            self.end_time = end_datetime.time()

        # Set cancelled_at timestamp when status changes to cancelled
        if self.status == self.Status.CANCELLED and not self.cancelled_at:
            self.cancelled_at = datetime.now()

        super().save(*args, **kwargs)

    def is_past(self):
        """Check if appointment is in the past"""
        appointment_datetime = datetime.combine(self.appointment_date, self.start_time)
        return appointment_datetime < datetime.now()

    def can_be_cancelled(self):
        """Check if appointment can still be cancelled"""
        return self.status in [self.Status.SCHEDULED, self.Status.CONFIRMED] and not self.is_past()


class AppointmentNote(models.Model):
    """
    Notes added to appointments (e.g., doctor's notes after visit)
    """
    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.CASCADE,
        related_name='appointment_notes'
    )
    author_id = models.IntegerField(help_text="User ID who wrote the note")
    author_type = models.CharField(
        max_length=20,
        choices=[('doctor', 'Doctor'), ('patient', 'Patient'), ('admin', 'Admin')]
    )
    note_text = models.TextField()
    is_private = models.BooleanField(
        default=False,
        help_text="If true, only visible to doctors and admins"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'appointment_notes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['appointment', 'created_at']),
        ]

    def __str__(self):
        return f"Note for Appointment {self.appointment.id} by {self.author_type} {self.author_id}"

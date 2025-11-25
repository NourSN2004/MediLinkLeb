"""
Doctor Service Models
Handles doctor profiles, working hours, and time-off management
"""
from django.db import models
from django.core.exceptions import ValidationError


class Doctor(models.Model):
    """
    Doctor profile extending user from Auth service
    Note: user_id references User in Auth Service (cross-service reference)
    """
    # Reference to User in Auth Service (not a ForeignKey for microservices)
    user_id = models.IntegerField(unique=True, primary_key=True)

    specialty = models.CharField(max_length=120, blank=True)
    license_number = models.CharField(max_length=80, unique=True, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'doctors'
        indexes = [
            models.Index(fields=['user_id']),
            models.Index(fields=['license_number']),
        ]

    def __str__(self):
        return f"Doctor {self.user_id} - {self.specialty}"


class DoctorWorkingHours(models.Model):
    """
    Doctor's weekly working schedule
    Defines availability for each day of the week
    """
    class DayOfWeek(models.IntegerChoices):
        MONDAY = 1, "Monday"
        TUESDAY = 2, "Tuesday"
        WEDNESDAY = 3, "Wednesday"
        THURSDAY = 4, "Thursday"
        FRIDAY = 5, "Friday"
        SATURDAY = 6, "Saturday"
        SUNDAY = 7, "Sunday"

    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name="working_hours"
    )
    day_of_week = models.IntegerField(choices=DayOfWeek.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        db_table = 'doctor_working_hours'
        unique_together = ("doctor", "day_of_week")
        ordering = ['day_of_week', 'start_time']
        indexes = [
            models.Index(fields=['doctor', 'day_of_week']),
        ]

    def clean(self):
        """Validate that start_time is before end_time"""
        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                raise ValidationError("Start time must be before end time")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Dr {self.doctor.user_id} – {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"


class DoctorTimeOff(models.Model):
    """
    Doctor's time-off periods (vacations, specific day blocks)
    Overrides working hours for specific dates
    """
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name="time_off"
    )
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    reason = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = 'doctor_time_off'
        ordering = ["date", "start_time"]
        indexes = [
            models.Index(fields=['doctor', 'date']),
        ]

    def clean(self):
        """Validate that start_time is before end_time"""
        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                raise ValidationError("Start time must be before end time")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Dr {self.doctor.user_id} off on {self.date} {self.start_time}-{self.end_time}"

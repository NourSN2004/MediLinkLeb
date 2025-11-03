# models.py
# MediLink — Sprint 1
# Custom database schema following the ER design

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator


# -----------------------------
# 1) USER (supertype)
# -----------------------------
class User(AbstractUser):
    # Define possible roles
    class Role(models.TextChoices):
        DOCTOR = "doctor", "Doctor"
        PATIENT = "patient", "Patient"
        PHARMACY = "pharmacy", "Pharmacy"

    email = models.EmailField(unique=True)           # Unique email for login
    name = models.CharField(max_length=120)          # Full name
    role = models.CharField(max_length=20, choices=Role.choices)
    phone_number = models.CharField(max_length=30, blank=True)
    reset_password_token = models.CharField(max_length=100, blank=True, null=True)
    reset_password_expires = models.DateTimeField(null=True, blank=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    def __str__(self):
        return f"{self.name} ({self.role})"


# -----------------------------
# 2) DOCTOR (subtype of User)
# -----------------------------
class Doctor(models.Model):
    doctor_id = models.OneToOneField(
        User, on_delete=models.CASCADE, primary_key=True, related_name="doctor"
    )
    specialty = models.CharField(max_length=120, blank=True)
    license_number = models.CharField(max_length=80, unique=True, blank=True, null=True)

    def __str__(self):
        return f"Dr. {self.doctor_id.name}"


# -----------------------------
# 3) PATIENT (subtype of User)
# -----------------------------
class Patient(models.Model):
    patient_id = models.OneToOneField(
        User, on_delete=models.CASCADE, primary_key=True, related_name="patient"
    )
    national_id = models.CharField(max_length=40, blank=True)
    dob = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, blank=True)
    blood_type = models.CharField(max_length=5, blank=True)
    history_summary = models.TextField(blank=True)

    def __str__(self):
        return self.patient_id.name


# -----------------------------
# 4) PHARMACY (subtype of User)
# -----------------------------
class Pharmacy(models.Model):
    pharmacy_id = models.OneToOneField(
        User, on_delete=models.CASCADE, primary_key=True, related_name="pharmacy"
    )
    address = models.CharField(max_length=255, blank=True)
    license_number = models.CharField(max_length=80, unique=True, blank=True, null=True)

    def __str__(self):
        return self.pharmacy_id.name


# -----------------------------
# 5) MEDICINE (global catalog)
# -----------------------------
class Medicine(models.Model):
    name = models.CharField(max_length=140)
    dosage_form = models.CharField(max_length=80)
    strength = models.CharField(max_length=80)
    description = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["name", "strength", "dosage_form"],
                name="uq_medicine_name_strength_form",
            )
        ]

    def __str__(self):
        return f"{self.name} {self.strength} ({self.dosage_form})"


# -----------------------------
# 6) DOCTOR WORKING HOURS
# -----------------------------
class DoctorWorkingHours(models.Model):
    # Days of the week (stored as numbers, displayed as text)
    class DayOfWeek(models.IntegerChoices):
        MON = 1, "Monday"
        TUE = 2, "Tuesday"
        WED = 3, "Wednesday"
        THU = 4, "Thursday"
        FRI = 5, "Friday"
        SAT = 6, "Saturday"
        SUN = 7, "Sunday"

    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="hours")
    day_of_week = models.IntegerField(choices=DayOfWeek.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        unique_together = ("doctor", "day_of_week")

    def __str__(self):
        return f"{self.doctor} – {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"


# -----------------------------
# 7) STOCK (Pharmacy ↔ Medicine)
# -----------------------------
class Stock(models.Model):
    pharmacy = models.ForeignKey(Pharmacy, on_delete=models.CASCADE, related_name="stocks")
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name="stocks")
    expiry_date = models.DateField()
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    quantity = models.IntegerField(validators=[MinValueValidator(0)])

    class Meta:
        unique_together = ("pharmacy", "medicine", "expiry_date")

    def __str__(self):
        return f"{self.pharmacy} – {self.medicine} (exp {self.expiry_date})"


# -----------------------------
# 8) APPOINTMENT (Doctor ↔ Patient)
# -----------------------------
class Appointment(models.Model):
    # Appointment status options
    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="appointments")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="appointments")
    date_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)
    doctor_notes = models.TextField(blank=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ("doctor", "patient", "date_time")

    def __str__(self):
        return f"{self.date_time} – {self.doctor} with {self.patient}"


# -----------------------------
# 9) PRESCRIBES (Doctor ↔ Patient ↔ Medicine)
# -----------------------------
class Prescribes(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="prescriptions_written")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="prescriptions_received")
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name="prescriptions")
    date_prescribed = models.DateField()
    dosage = models.CharField(max_length=120)
    duration = models.CharField(max_length=120)
    extra_notes = models.TextField(blank=True)

    class Meta:
        unique_together = ("doctor", "patient", "medicine", "date_prescribed")

    def __str__(self):
        return f"{self.medicine} for {self.patient} by {self.doctor} on {self.date_prescribed}"

# -----------------------------
# 10) PATIENT TEST RESULTS (multivalued attribute)
# -----------------------------
class PatientTestResult(models.Model):
    patient = models.ForeignKey('Patient', on_delete=models.CASCADE, related_name='test_results')
    test_result = models.FileField(upload_to='test_results/')  # path stored in DB, file saved under MEDIA_ROOT/test_results/

    def __str__(self):
        return f"Test Result for {self.patient}"


# -----------------------------
# 11) DOCTOR TIME OFF (specific date blocks)
# -----------------------------
class DoctorTimeOff(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="time_off")
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    reason = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["date", "start_time"]

    def __str__(self):
        return f"Time off {self.date} {self.start_time}-{self.end_time} ({self.doctor})"

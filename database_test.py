import os, sys, django
from datetime import date, datetime, time
from django.utils import timezone
# locate manage.py automatically
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)                 # one level up (where manage.py is)
INNER_PROJECT = os.path.join(CURRENT_DIR, "MediLinkLeb")    # where settings.py lives

# put both on Python’s search path
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, CURRENT_DIR)
sys.path.insert(0, INNER_PROJECT)

# tell Django where to find settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MediLinkLeb.settings")

django.setup()

from accounts.models import (
    User, Doctor, Patient, Pharmacy,
    Medicine, Stock, Appointment,
    Prescribes, DoctorWorkingHours
)

print("\n=== MediLink Database Test Script (Fresh Values) ===\n")

# -----------------------------
# 1) Create sample Users
# -----------------------------
doctor_user = User.objects.create_user(
    username="dr_miller",
    email="miller@example.com",
    name="Dr. Alex Miller",
    role=User.Role.DOCTOR,
    password="test1234"
)

patient_user = User.objects.create_user(
    username="patient_lina",
    email="lina@example.com",
    name="Lina Khoury",
    role=User.Role.PATIENT,
    password="test1234"
)

pharmacy_user = User.objects.create_user(
    username="pharma_green",
    email="greenpharma@example.com",
    name="GreenLife Pharmacy",
    role=User.Role.PHARMACY,
    password="test1234"
)

print("✅ Created new sample users.")

# -----------------------------
# 2) Create Doctor, Patient, Pharmacy subtypes
# -----------------------------
doctor = Doctor.objects.create(
    doctor_id=doctor_user,
    specialty="Neurology",
    license_number="DOC98765"
)
patient = Patient.objects.create(
    patient_id=patient_user,
    national_id="PX00987",
    gender="Female",
    blood_type="O-"
)
pharmacy = Pharmacy.objects.create(
    pharmacy_id=pharmacy_user,
    address="Hamra Street, Beirut",
    license_number="PH009"
)

print("✅ Linked subtypes successfully.")

# -----------------------------
# 3) Add Medicines
# -----------------------------
paracetamol = Medicine.objects.create(
    name="Paracetamol",
    dosage_form="Tablet",
    strength="500 mg",
    description="Pain and fever reducer"
)
ibuprofen = Medicine.objects.create(
    name="Ibuprofen",
    dosage_form="Capsule",
    strength="200 mg",
    description="Anti-inflammatory"
)

print("✅ Medicines added.")

# -----------------------------
# 4) Add Doctor Working Hours
# -----------------------------
DoctorWorkingHours.objects.create(
    doctor=doctor,
    day_of_week=DoctorWorkingHours.DayOfWeek.TUE,
    start_time=time(8, 30),
    end_time=time(12, 30)
)
DoctorWorkingHours.objects.create(
    doctor=doctor,
    day_of_week=DoctorWorkingHours.DayOfWeek.THU,
    start_time=time(10, 0),
    end_time=time(15, 0)
)

print("✅ Doctor working hours added.")

# -----------------------------
# 5) Add Stock for Pharmacy
# -----------------------------
Stock.objects.create(
    pharmacy=pharmacy,
    medicine=paracetamol,
    expiry_date=date(2026, 8, 1),
    price=2.75,
    quantity=180
)
Stock.objects.create(
    pharmacy=pharmacy,
    medicine=ibuprofen,
    expiry_date=date(2025, 11, 20),
    price=4.25,
    quantity=120
)

print("✅ Pharmacy stock added.")

# -----------------------------
# 6) Add Appointment
# -----------------------------
appt = Appointment.objects.create(
    doctor=doctor,
    patient=patient,
    date_time=timezone.make_aware(datetime(2025, 11, 10, 11, 45)),
    status=Appointment.Status.SCHEDULED,
    doctor_notes="Neurological evaluation."
)
print("✅ Appointment created:", appt)

# -----------------------------
# 7) Add Prescription
# -----------------------------
Prescribes.objects.create(
    doctor=doctor,
    patient=patient,
    medicine=paracetamol,
    date_prescribed=date(2025, 11, 9),
    dosage="500 mg",
    duration="5 days",
    extra_notes="Take every 6 hours"
)

print("✅ Prescription recorded.")

# -----------------------------
# 8) Query tests
# -----------------------------
print("\n--- Query Tests ---")
print("All Doctors:", list(Doctor.objects.values_list("doctor_id__name", flat=True)))
print("All Patients:", list(Patient.objects.values_list("patient_id__name", flat=True)))
print("Medicines in Pharmacy:", list(pharmacy.stocks.values_list("medicine__name", flat=True)))
print("Doctor’s Appointments:", list(doctor.appointments.values_list("patient__patient_id__name", "date_time")))
print("Prescriptions for patient:", list(patient.prescriptions_received.values_list("medicine__name", "dosage")))

print("\n✅ All tests ran successfully!\n")

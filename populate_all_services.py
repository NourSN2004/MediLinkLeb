"""
Populate all microservices with sample data
Run this inside each service container
"""
import os
import sys
import django

# Determine settings module based on service
if os.path.exists('doctors'):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'doctor_service.settings')
elif os.path.exists('patients'):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'patient_service.settings')
elif os.path.exists('pharmacies'):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pharmacy_service.settings')
else:
    print("❌ Unknown service")
    sys.exit(1)

# Setup Django
django.setup()

from datetime import date, time, timedelta

# Determine which service this is running in
if 'doctors' in sys.modules or os.path.exists('doctors'):
    # Doctor Service
    from doctors.models import Doctor, DoctorWorkingHours
    
    print("🏥 Populating Doctor Service...")
    
    # Create sample doctors
    doctors_data = [
        {
            'email': 'doctor1@medilink.com',
            'first_name': 'Sarah',
            'last_name': 'Johnson',
            'specialty': 'Cardiology',
            'license_number': 'LIC-CARD-001',
            'phone': '0551234567',
            'bio': 'Experienced cardiologist with 15 years of practice',
            'consultation_fee': 150.00,
        },
        {
            'email': 'doctor2@medilink.com',
            'first_name': 'Michael',
            'last_name': 'Chen',
            'specialty': 'Pediatrics',
            'license_number': 'LIC-PED-002',
            'phone': '0552345678',
            'bio': 'Specialist in pediatric care and child development',
            'consultation_fee': 120.00,
        },
        {
            'email': 'doctor3@medilink.com',
            'first_name': 'Emily',
            'last_name': 'Rodriguez',
            'specialty': 'Dermatology',
            'license_number': 'LIC-DERM-003',
            'phone': '0553456789',
            'bio': 'Expert in skin conditions and cosmetic dermatology',
            'consultation_fee': 130.00,
        },
        {
            'email': 'doctor4@medilink.com',
            'first_name': 'David',
            'last_name': 'Patel',
            'specialty': 'Orthopedics',
            'license_number': 'LIC-ORTH-004',
            'phone': '0554567890',
            'bio': 'Orthopedic surgeon specializing in sports injuries',
            'consultation_fee': 180.00,
        },
        {
            'email': 'doctor5@medilink.com',
            'first_name': 'Lisa',
            'last_name': 'Anderson',
            'specialty': 'General Practice',
            'license_number': 'LIC-GP-005',
            'phone': '0555678901',
            'bio': 'Family doctor with comprehensive medical care',
            'consultation_fee': 100.00,
        },
    ]
    
    created_count = 0
    for data in doctors_data:
        doctor, created = Doctor.objects.get_or_create(
            email=data['email'],
            defaults=data
        )
        if created:
            created_count += 1
            
            # Add working hours (Monday-Friday, 9AM-5PM)
            for day in range(1, 6):  # Monday=1 to Friday=5
                DoctorWorkingHours.objects.get_or_create(
                    doctor=doctor,
                    day_of_week=day,
                    defaults={
                        'start_time': time(9, 0),
                        'end_time': time(17, 0),
                    }
                )
    
    print(f"✅ Created {created_count} doctors with working hours")
    print(f"📊 Total doctors: {Doctor.objects.count()}")

elif 'patients' in sys.modules or os.path.exists('patients'):
    # Patient Service
    from patients.models import Patient
    
    print("🏥 Populating Patient Service...")
    
    patients_data = [
        {
            'email': 'patient1@medilink.com',
            'first_name': 'John',
            'last_name': 'Smith',
            'phone': '0556789012',
            'date_of_birth': date(1985, 5, 15),
            'gender': 'male',
            'blood_type': 'A+',
            'address': '123 Main St, Beirut',
        },
        {
            'email': 'patient2@medilink.com',
            'first_name': 'Maria',
            'last_name': 'Garcia',
            'phone': '0557890123',
            'date_of_birth': date(1990, 8, 22),
            'gender': 'female',
            'blood_type': 'O+',
            'address': '456 Oak Ave, Beirut',
        },
        {
            'email': 'patient3@medilink.com',
            'first_name': 'Ahmed',
            'last_name': 'Hassan',
            'phone': '0558901234',
            'date_of_birth': date(1978, 3, 10),
            'gender': 'male',
            'blood_type': 'B+',
            'address': '789 Cedar Rd, Beirut',
        },
        {
            'email': 'patient4@medilink.com',
            'first_name': 'Layla',
            'last_name': 'Khoury',
            'phone': '0559012345',
            'date_of_birth': date(1995, 11, 5),
            'gender': 'female',
            'blood_type': 'AB+',
            'address': '321 Pine St, Beirut',
        },
        {
            'email': 'patient5@medilink.com',
            'first_name': 'Omar',
            'last_name': 'Mansour',
            'phone': '0550123456',
            'date_of_birth': date(2000, 1, 30),
            'gender': 'male',
            'blood_type': 'A-',
            'address': '654 Elm Blvd, Beirut',
        },
    ]
    
    created_count = 0
    for data in patients_data:
        patient, created = Patient.objects.get_or_create(
            email=data['email'],
            defaults=data
        )
        if created:
            created_count += 1
    
    print(f"✅ Created {created_count} patients")
    print(f"📊 Total patients: {Patient.objects.count()}")

elif 'pharmacies' in sys.modules or os.path.exists('pharmacies'):
    # Pharmacy Service
    from pharmacies.models import Pharmacy
    
    print("🏥 Populating Pharmacy Service...")
    
    pharmacies_data = [
        {
            'email': 'pharmacy1@medilink.com',
            'name': 'HealthPlus Pharmacy',
            'phone': '0551112222',
            'license_number': 'PHARM-LIC-001',
            'address': '100 Health St, Beirut',
            'city': 'Beirut',
        },
        {
            'email': 'pharmacy2@medilink.com',
            'name': 'CareWell Pharmacy',
            'phone': '0552223333',
            'license_number': 'PHARM-LIC-002',
            'address': '200 Care Ave, Tripoli',
            'city': 'Tripoli',
        },
        {
            'email': 'pharmacy3@medilink.com',
            'name': 'MediCare Pharmacy',
            'phone': '0553334444',
            'license_number': 'PHARM-LIC-003',
            'address': '300 Medicine Rd, Sidon',
            'city': 'Sidon',
        },
    ]
    
    created_count = 0
    for data in pharmacies_data:
        pharmacy, created = Pharmacy.objects.get_or_create(
            email=data['email'],
            defaults=data
        )
        if created:
            created_count += 1
    
    print(f"✅ Created {created_count} pharmacies")
    print(f"📊 Total pharmacies: {Pharmacy.objects.count()}")

else:
    print("❌ Unknown service - cannot populate data")
    sys.exit(1)

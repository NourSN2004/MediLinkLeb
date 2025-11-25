from doctors.models import Doctor, DoctorWorkingHours
from datetime import time

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
        for day in range(1, 6):
            DoctorWorkingHours.objects.get_or_create(
                doctor=doctor,
                day_of_week=day,
                defaults={
                    'start_time': time(9, 0),
                    'end_time': time(17, 0),
                }
            )

print(f"✅ Created {created_count} doctors")
print(f"📊 Total: {Doctor.objects.count()}")

"""
Create test users directly in the database via Django ORM
Run this inside the auth-service pod
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auth_service.settings')
django.setup()

from accounts.models import User

print("=" * 60)
print("  Creating Test Users")
print("=" * 60)

users_data = [
    {
        "username": "doctor1",
        "email": "doctor1@medilink.com",
        "password": "Password123!",
        "name": "Dr. John Smith",
        "role": "doctor",
        "phone_number": "+96170123456",
        "email_verified": True
    },
    {
        "username": "patient1",
        "email": "patient1@medilink.com",
        "password": "Password123!",
        "name": "Jane Doe",
        "role": "patient",
        "phone_number": "+96170234567",
        "email_verified": True
    },
    {
        "username": "pharmacy1",
        "email": "pharmacy1@medilink.com",
        "password": "Password123!",
        "name": "City Pharmacy",
        "role": "pharmacy",
        "phone_number": "+96170345678",
        "email_verified": True
    }
]

created_count = 0
existing_count = 0

for user_data in users_data:
    password = user_data.pop('password')
    
    user, created = User.objects.get_or_create(
        email=user_data['email'],
        defaults=user_data
    )
    
    if created:
        user.set_password(password)
        user.save()
        created_count += 1
        print(f"✓ Created {user_data['role']}: {user_data['email']}")
    else:
        existing_count += 1
        print(f"⚠ Already exists: {user_data['email']}")

print("\n" + "=" * 60)
print(f"  Created: {created_count} | Already existed: {existing_count}")
print("=" * 60)
print("\nTest Credentials:")
print("-" * 60)
print("\nDOCTOR:")
print("  Email: doctor1@medilink.com")
print("  Password: Password123!")
print("\nPATIENT:")
print("  Email: patient1@medilink.com")
print("  Password: Password123!")
print("\nPHARMACY:")
print("  Email: pharmacy1@medilink.com")
print("  Password: Password123!")
print("\n" + "=" * 60)

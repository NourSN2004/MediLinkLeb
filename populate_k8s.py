"""
Population script for Kubernetes deployment
Creates test users via Auth Service API
"""
import requests
import json
from datetime import datetime, time

# Auth service URL (accessible from within the cluster)
AUTH_SERVICE_URL = "http://localhost:8001"

print("=" * 60)
print("  MediLink - Kubernetes Database Population")
print("=" * 60)

# Test users to create
users_data = [
    {
        "username": "doctor1",
        "email": "doctor1@medilink.com",
        "password": "Password123!",
        "name": "Dr. John Smith",
        "role": "doctor",
        "phone_number": "+96170123456"
    },
    {
        "username": "patient1",
        "email": "patient1@medilink.com",
        "password": "Password123!",
        "name": "Jane Doe",
        "role": "patient",
        "phone_number": "+96170234567"
    },
    {
        "username": "pharmacy1",
        "email": "pharmacy1@medilink.com",
        "password": "Password123!",
        "name": "City Pharmacy",
        "role": "pharmacy",
        "phone_number": "+96170345678"
    }
]

print("\n📝 Creating test users...")
created_users = []

for user_data in users_data:
    print(f"\n  Creating {user_data['role']}: {user_data['email']}")
    try:
        response = requests.post(
            f"{AUTH_SERVICE_URL}/api/register/",
            json=user_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            print(f"    ✓ Created successfully")
            created_users.append(user_data)
        elif response.status_code == 400 and "already exists" in response.text.lower():
            print(f"    ⚠ Already exists")
            created_users.append(user_data)
        else:
            print(f"    ✗ Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"    ✗ Error: {str(e)}")

print("\n" + "=" * 60)
print("  Summary")
print("=" * 60)
print(f"\n✓ Users created/verified: {len(created_users)}")
print("\nTest Credentials:")
print("-" * 60)
for user in created_users:
    print(f"\n{user['role'].upper()}")
    print(f"  Email: {user['email']}")
    print(f"  Password: {user['password']}")

print("\n" + "=" * 60)
print("  Access the application at: http://localhost:8080")
print("=" * 60)

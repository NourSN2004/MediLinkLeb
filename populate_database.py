"""
Population script for Kubernetes deployment
Creates test users via API Gateway
"""
import requests
import json
import time
import sys

# Use the port-forward endpoint
API_GATEWAY_URL = "http://localhost:8888"

print("=" * 60)
print("  MediLink - Database Population via API Gateway")
print("=" * 60)
print("\nMake sure kubectl port-forward is running on port 8888!")
print("=" * 60)

# Wait a moment to let user check
time.sleep(2)

# Test users to create
users_data = [
    {
        "username": "doctor1",
        "email": "doctor1@medilink.com",
        "password": "Password123!",
        "password2": "Password123!",
        "first_name": "John",
        "last_name": "Smith",
        "role": "doctor",
        "phone_number": "+96170123456",
        "license_number": "DOC001",
        "specialization": "General Practice"
    },
    {
        "username": "patient1",
        "email": "patient1@medilink.com",
        "password": "Password123!",
        "password2": "Password123!",
        "first_name": "Jane",
        "last_name": "Doe",
        "role": "patient",
        "phone_number": "+96170234567",
        "date_of_birth": "1990-01-15",
        "gender": "F"
    },
    {
        "username": "pharmacy1",
        "email": "pharmacy1@medilink.com",
        "password": "Password123!",
        "password2": "Password123!",
        "first_name": "City",
        "last_name": "Pharmacy",
        "role": "pharmacy",
        "phone_number": "+96170345678",
        "license_number": "PHAR001",
        "address": "Main Street, Beirut"
    }
]

print("\n📝 Creating test users...")
created_users = []

for user_data in users_data:
    print(f"\n  Creating {user_data['role']}: {user_data['email']}")
    try:
        # First, get the signup page to establish session
        session = requests.Session()
        
        # Post to signup endpoint
        response = session.post(
            f"{API_GATEWAY_URL}/signup/step2/",
            data=user_data,
            timeout=10,
            allow_redirects=False
        )
        
        if response.status_code in [200, 201, 302]:
            print(f"    ✓ Created successfully (Status: {response.status_code})")
            created_users.append(user_data)
        elif response.status_code == 400:
            print(f"    ⚠ May already exist or validation error")
            print(f"    Response: {response.text[:200]}")
        else:
            print(f"    ✗ Failed: {response.status_code}")
            if len(response.text) < 500:
                print(f"    Response: {response.text}")
    except requests.exceptions.ConnectionError:
        print(f"    ✗ Connection Error: Is kubectl port-forward running on port 8888?")
        print("\n    Run this command in another terminal:")
        print("    kubectl port-forward -n medilink service/api-gateway 8888:8000")
        sys.exit(1)
    except Exception as e:
        print(f"    ✗ Error: {str(e)}")

print("\n" + "=" * 60)
print("  Summary")
print("=" * 60)
print(f"\n✓ Users processed: {len(created_users)}")

if created_users:
    print("\nTest Credentials:")
    print("-" * 60)
    for user in created_users:
        print(f"\n{user['role'].upper()}")
        print(f"  Email: {user['email']}")
        print(f"  Password: {user['password']}")
        print(f"  Username: {user['username']}")

print("\n" + "=" * 60)
print("  Access Points:")
print("=" * 60)
print(f"  Port-forward:  http://localhost:8888")
print(f"  Ingress:       http://medilink.local (requires minikube tunnel)")
print("=" * 60)

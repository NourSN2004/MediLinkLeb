# MediLink Microservices - Complete Testing Guide

This guide provides step-by-step instructions to test every component of the MediLink microservices implementation.

---

## Table of Contents
1. [Prerequisites Check](#prerequisites-check)
2. [Initial Deployment](#initial-deployment)
3. [Infrastructure Testing](#infrastructure-testing)
4. [Auth Service Testing](#auth-service-testing)
5. [Doctor Service Testing](#doctor-service-testing)
6. [Inter-Service Communication Testing](#inter-service-communication-testing)
7. [Advanced Features Testing](#advanced-features-testing)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites Check

### Step 1: Verify Minikube Installation
```bash
# Check if minikube is installed
minikube version

# Expected output: minikube version: v1.x.x
```

### Step 2: Verify Docker Installation
```bash
# Check Docker
docker --version

# Expected output: Docker version 20.x.x or higher
```

### Step 3: Verify kubectl Installation
```bash
# Check kubectl
kubectl version --client

# Expected output: Client Version: v1.x.x
```

### Step 4: Check Current Directory
```bash
# Make sure you're in the project root
pwd

# Expected: /home/user/MediLinkLeb-Copy or similar
# You should see the microservices/ and k8s/ directories
ls -la
```

---

## Initial Deployment

### Step 1: Start Minikube
```bash
# Start minikube with sufficient resources
minikube start --cpus=4 --memory=8192 --disk-size=20g

# Wait for minikube to be ready (this may take 2-3 minutes)
# Expected output: "Done! kubectl is now configured to use "minikube"..."
```

### Step 2: Verify Minikube is Running
```bash
# Check minikube status
minikube status

# Expected output:
# minikube: Running
# cluster: Running
# kubectl: Correctly Configured
```

### Step 3: Configure Docker Environment
```bash
# Point Docker to minikube's Docker daemon
eval $(minikube docker-env)

# Verify by checking Docker images
docker images
```

### Step 4: Run Full Deployment Script
```bash
# Make the script executable
chmod +x scripts/full-deploy.sh

# Run the deployment (this takes 10-15 minutes)
./scripts/full-deploy.sh

# The script will:
# 1. Create namespace
# 2. Build all Docker images
# 3. Deploy database
# 4. Deploy all services
# 5. Run migrations
# 6. Show final status
```

**What to expect during deployment:**
- Image building: ~5 minutes (you'll see "Building auth-service image...", etc.)
- Database deployment: ~2 minutes (waiting for PostgreSQL to be ready)
- Service deployment: ~3 minutes (deploying all 8 services)
- Migrations: ~1 minute (running Django migrations)

---

## Infrastructure Testing

### Test 1: Verify Namespace
```bash
# Check if medilink namespace exists
kubectl get namespace medilink

# Expected output:
# NAME       STATUS   AGE
# medilink   Active   Xm
```

### Test 2: Verify All Pods are Running
```bash
# List all pods in medilink namespace
kubectl get pods -n medilink

# Expected output: 29 pods total (all should show "Running" or "Completed")
# - postgres-0: 1 pod
# - api-gateway: 4 pods
# - auth-service: 3 pods
# - doctor-service: 3 pods
# - patient-service: 4 pods
# - pharmacy-service: 2 pods
# - scheduling-service: 4 pods
# - inventory-service: 3 pods
# - notification-service: 2 pods
# - Migration jobs: 7 completed pods
```

**If pods are not running:**
```bash
# Check specific pod status
kubectl describe pod <pod-name> -n medilink

# Check pod logs
kubectl logs <pod-name> -n medilink
```

### Test 3: Verify All Services
```bash
# List all services
kubectl get services -n medilink

# Expected output: 9 services
# - postgres-service (ClusterIP)
# - api-gateway-service (NodePort)
# - auth-service (ClusterIP)
# - doctor-service (ClusterIP)
# - patient-service (ClusterIP)
# - pharmacy-service (ClusterIP)
# - scheduling-service (ClusterIP)
# - inventory-service (ClusterIP)
# - notification-service (ClusterIP)
```

### Test 4: Get API Gateway URL
```bash
# Get the API Gateway URL
minikube service api-gateway-service -n medilink --url

# Expected output: http://192.168.49.2:XXXXX
# Copy this URL - you'll use it for all API calls
# Example: http://192.168.49.2:31234
```

**Store this URL in a variable for convenience:**
```bash
export API_URL=$(minikube service api-gateway-service -n medilink --url)
echo "API Gateway URL: $API_URL"
```

### Test 5: Verify Database
```bash
# Check if PostgreSQL is running
kubectl get pods -n medilink -l app=postgres

# Expected output: postgres-0 should be Running

# Test database connection
kubectl exec -it postgres-0 -n medilink -- psql -U medilink -d medilink_db -c "SELECT 1;"

# Expected output:
#  ?column?
# ----------
#         1
# (1 row)
```

---

## Auth Service Testing

### Test 1: Health Check
```bash
# Test auth service health endpoint
kubectl run curl-test --image=curlimages/curl -i --rm --restart=Never -n medilink -- \
  curl -s http://auth-service:8000/health/

# Expected output: {"status": "healthy"}
```

### Test 2: Register a New User
```bash
# Register a doctor user
curl -X POST "$API_URL/api/auth/register/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "dr_smith",
    "email": "drsmith@example.com",
    "password": "SecurePass123!",
    "password2": "SecurePass123!",
    "first_name": "John",
    "last_name": "Smith",
    "role": "doctor"
  }'

# Expected output:
# {
#   "user": {
#     "id": 1,
#     "username": "dr_smith",
#     "email": "drsmith@example.com",
#     "first_name": "John",
#     "last_name": "Smith",
#     "role": "doctor"
#   },
#   "message": "User registered successfully"
# }
```

### Test 3: Login and Get Token
```bash
# Login to get JWT token
curl -X POST "$API_URL/api/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "dr_smith",
    "password": "SecurePass123!"
  }'

# Expected output:
# {
#   "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
#   "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
# }

# SAVE THE ACCESS TOKEN - you'll need it for authenticated requests
```

**Store the token for later use:**
```bash
# After running the login command, copy the access token and run:
export TOKEN="<paste-your-access-token-here>"

# Example:
# export TOKEN="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzMxOTYxMjAwLCJpYXQiOjE3MzE5NTc2MDAsImp0aSI6ImFiYzEyMyIsInVzZXJfaWQiOjF9.xyz"
```

### Test 4: Get User Profile
```bash
# Get current user profile (requires token)
curl -X GET "$API_URL/api/auth/profile/" \
  -H "Authorization: Bearer $TOKEN"

# Expected output:
# {
#   "id": 1,
#   "username": "dr_smith",
#   "email": "drsmith@example.com",
#   "first_name": "John",
#   "last_name": "Smith",
#   "role": "doctor",
#   "is_active": true
# }
```

### Test 5: List All Users (Admin Function)
```bash
# List all users
curl -X GET "$API_URL/api/auth/users/" \
  -H "Authorization: Bearer $TOKEN"

# Expected output: Array of user objects
```

### Test 6: Register More Test Users
```bash
# Register a patient user
curl -X POST "$API_URL/api/auth/register/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "patient_jane",
    "email": "jane@example.com",
    "password": "SecurePass123!",
    "password2": "SecurePass123!",
    "first_name": "Jane",
    "last_name": "Doe",
    "role": "patient"
  }'

# Register another doctor
curl -X POST "$API_URL/api/auth/register/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "dr_jones",
    "email": "drjones@example.com",
    "password": "SecurePass123!",
    "password2": "SecurePass123!",
    "first_name": "Emily",
    "last_name": "Jones",
    "role": "doctor"
  }'
```

---

## Doctor Service Testing

### Test 1: Health Check
```bash
# Test doctor service health
kubectl run curl-test --image=curlimages/curl -i --rm --restart=Never -n medilink -- \
  curl -s http://doctor-service:8000/health/

# Expected output: {"status": "healthy"}
```

### Test 2: Create Doctor Profile
```bash
# Create doctor profile for dr_smith (user_id=1)
curl -X POST "$API_URL/api/doctors/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "user_id": 1,
    "specialty": "Cardiology",
    "license_number": "MD12345"
  }'

# Expected output:
# {
#   "user_id": 1,
#   "user_info": {
#     "username": "dr_smith",
#     "email": "drsmith@example.com",
#     "first_name": "John",
#     "last_name": "Smith"
#   },
#   "specialty": "Cardiology",
#   "license_number": "MD12345",
#   "created_at": "2025-11-18T...",
#   "updated_at": "2025-11-18T..."
# }
```

### Test 3: Get Doctor Profile
```bash
# Get doctor profile by user_id
curl -X GET "$API_URL/api/doctors/1/" \
  -H "Authorization: Bearer $TOKEN"

# Expected output: Doctor profile with user info
```

### Test 4: List All Doctors
```bash
# List all doctors
curl -X GET "$API_URL/api/doctors/" \
  -H "Authorization: Bearer $TOKEN"

# Expected output: Array of doctor profiles
```

### Test 5: Update Doctor Profile
```bash
# Update doctor specialty
curl -X PATCH "$API_URL/api/doctors/1/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "specialty": "Interventional Cardiology"
  }'

# Expected output: Updated doctor profile
```

### Test 6: Add Working Hours
```bash
# Add Monday working hours (9 AM - 5 PM)
curl -X POST "$API_URL/api/doctors/1/working-hours/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "day_of_week": 1,
    "start_time": "09:00:00",
    "end_time": "17:00:00"
  }'

# Expected output:
# {
#   "id": 1,
#   "doctor": 1,
#   "day_of_week": 1,
#   "day_of_week_display": "Monday",
#   "start_time": "09:00:00",
#   "end_time": "17:00:00"
# }

# Add Tuesday working hours
curl -X POST "$API_URL/api/doctors/1/working-hours/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "day_of_week": 2,
    "start_time": "09:00:00",
    "end_time": "17:00:00"
  }'

# Add Wednesday working hours
curl -X POST "$API_URL/api/doctors/1/working-hours/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "day_of_week": 3,
    "start_time": "09:00:00",
    "end_time": "17:00:00"
  }'

# Add Friday half-day (9 AM - 1 PM)
curl -X POST "$API_URL/api/doctors/1/working-hours/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "day_of_week": 5,
    "start_time": "09:00:00",
    "end_time": "13:00:00"
  }'
```

### Test 7: List Doctor's Working Hours
```bash
# Get all working hours for doctor
curl -X GET "$API_URL/api/doctors/1/working-hours/" \
  -H "Authorization: Bearer $TOKEN"

# Expected output: Array of working hours
```

### Test 8: Update Working Hours
```bash
# Update Monday hours to 8 AM - 6 PM
curl -X PATCH "$API_URL/api/doctors/1/working-hours/1/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "start_time": "08:00:00",
    "end_time": "18:00:00"
  }'

# Expected output: Updated working hours
```

### Test 9: Add Time-Off Period
```bash
# Add time-off for lunch break on a specific date
# First, get tomorrow's date:
TOMORROW=$(date -d "+1 day" +%Y-%m-%d)

curl -X POST "$API_URL/api/doctors/1/time-off/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{
    \"date\": \"$TOMORROW\",
    \"start_time\": \"12:00:00\",
    \"end_time\": \"13:00:00\",
    \"reason\": \"Lunch break\"
  }"

# Expected output:
# {
#   "id": 1,
#   "doctor": 1,
#   "date": "2025-11-19",
#   "start_time": "12:00:00",
#   "end_time": "13:00:00",
#   "reason": "Lunch break"
# }

# Add a vacation day
NEXT_WEEK=$(date -d "+7 days" +%Y-%m-%d)
curl -X POST "$API_URL/api/doctors/1/time-off/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{
    \"date\": \"$NEXT_WEEK\",
    \"start_time\": \"00:00:00\",
    \"end_time\": \"23:59:59\",
    \"reason\": \"Vacation\"
  }"
```

### Test 10: List Time-Off Periods
```bash
# Get all time-off periods for doctor
curl -X GET "$API_URL/api/doctors/1/time-off/" \
  -H "Authorization: Bearer $TOKEN"

# Expected output: Array of time-off periods
```

### Test 11: Calculate Available Slots (MOST IMPORTANT TEST)
```bash
# Get available time slots for tomorrow
TOMORROW=$(date -d "+1 day" +%Y-%m-%d)

curl -X GET "$API_URL/api/doctors/1/availability/?date=$TOMORROW&duration=30" \
  -H "Authorization: Bearer $TOKEN"

# Expected output:
# {
#   "doctor_id": 1,
#   "date": "2025-11-19",
#   "day_of_week": "Monday",
#   "duration_minutes": 30,
#   "working_hours": {
#     "start": "08:00:00",
#     "end": "18:00:00"
#   },
#   "time_off_periods": [
#     {
#       "start": "12:00:00",
#       "end": "13:00:00",
#       "reason": "Lunch break"
#     }
#   ],
#   "available_slots": [
#     {"start": "08:00:00", "end": "08:30:00"},
#     {"start": "08:15:00", "end": "08:45:00"},
#     {"start": "08:30:00", "end": "09:00:00"},
#     ... (slots continue in 15-minute increments)
#     {"start": "11:45:00", "end": "12:15:00"},
#     // Lunch break from 12:00-13:00 is excluded
#     {"start": "13:00:00", "end": "13:30:00"},
#     ... (continues until 18:00)
#   ]
# }
```

**Test with different durations:**
```bash
# 15-minute appointments
curl -X GET "$API_URL/api/doctors/1/availability/?date=$TOMORROW&duration=15" \
  -H "Authorization: Bearer $TOKEN"

# 60-minute appointments
curl -X GET "$API_URL/api/doctors/1/availability/?date=$TOMORROW&duration=60" \
  -H "Authorization: Bearer $TOKEN"

# Test for a day with no working hours (should return empty slots)
SUNDAY=$(date -d "next Sunday" +%Y-%m-%d)
curl -X GET "$API_URL/api/doctors/1/availability/?date=$SUNDAY&duration=30" \
  -H "Authorization: Bearer $TOKEN"

# Expected output: "available_slots": []
```

### Test 12: Search Doctors by Specialty
```bash
# Search for cardiologists
curl -X GET "$API_URL/api/doctors/search/?specialty=Cardiology" \
  -H "Authorization: Bearer $TOKEN"

# Expected output: Array of doctors matching specialty
```

---

## Inter-Service Communication Testing

### Test 1: Verify Doctor Service Calls Auth Service
```bash
# This is already tested when creating a doctor profile
# The doctor service fetches user info from auth service

# Create another doctor to verify
# First, register a new doctor user
curl -X POST "$API_URL/api/auth/register/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "dr_brown",
    "email": "drbrown@example.com",
    "password": "SecurePass123!",
    "password2": "SecurePass123!",
    "first_name": "Michael",
    "last_name": "Brown",
    "role": "doctor"
  }'

# Get the user_id from response (let's say it's 3)
# Create doctor profile
curl -X POST "$API_URL/api/doctors/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "user_id": 3,
    "specialty": "Neurology",
    "license_number": "MD54321"
  }'

# The response should include user_info fetched from Auth Service
# This proves inter-service communication works
```

### Test 2: Check Service Communication from Inside Cluster
```bash
# Connect to a pod and test internal service URLs
kubectl exec -it $(kubectl get pod -n medilink -l app=auth-service -o jsonpath="{.items[0].metadata.name}") -n medilink -- /bin/sh

# Inside the pod, run:
# curl http://doctor-service:8000/health/
# curl http://auth-service:8000/health/
# exit
```

---

## Advanced Features Testing

### Test 1: Complex Availability Calculation
```bash
# Create a complex schedule with multiple time-off periods
TOMORROW=$(date -d "+1 day" +%Y-%m-%d)

# Add morning break
curl -X POST "$API_URL/api/doctors/1/time-off/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{
    \"date\": \"$TOMORROW\",
    \"start_time\": \"10:00:00\",
    \"end_time\": \"10:15:00\",
    \"reason\": \"Morning break\"
  }"

# Add afternoon break
curl -X POST "$API_URL/api/doctors/1/time-off/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{
    \"date\": \"$TOMORROW\",
    \"start_time\": \"15:00:00\",
    \"end_time\": \"15:30:00\",
    \"reason\": \"Afternoon break\"
  }"

# Now check availability - should exclude all break times
curl -X GET "$API_URL/api/doctors/1/availability/?date=$TOMORROW&duration=30" \
  -H "Authorization: Bearer $TOKEN"

# Verify that slots from 10:00-10:15, 12:00-13:00, and 15:00-15:30 are excluded
```

### Test 2: Edge Cases

**Test invalid time range:**
```bash
# Try to create working hours with start > end (should fail)
curl -X POST "$API_URL/api/doctors/1/working-hours/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "day_of_week": 4,
    "start_time": "17:00:00",
    "end_time": "09:00:00"
  }'

# Expected: Validation error
```

**Test duplicate working hours:**
```bash
# Try to create duplicate Monday hours (should fail - unique constraint)
curl -X POST "$API_URL/api/doctors/1/working-hours/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "day_of_week": 1,
    "start_time": "10:00:00",
    "end_time": "16:00:00"
  }'

# Expected: Unique constraint error
```

**Test availability on past date:**
```bash
# Request availability for yesterday
YESTERDAY=$(date -d "-1 day" +%Y-%m-%d)
curl -X GET "$API_URL/api/doctors/1/availability/?date=$YESTERDAY&duration=30" \
  -H "Authorization: Bearer $TOKEN"

# Should still work (no validation preventing past dates)
```

### Test 3: Authentication and Authorization

**Test without token:**
```bash
# Try to access protected endpoint without token
curl -X GET "$API_URL/api/doctors/"

# Expected: 401 Unauthorized
```

**Test with invalid token:**
```bash
# Try with invalid token
curl -X GET "$API_URL/api/doctors/" \
  -H "Authorization: Bearer invalid_token_here"

# Expected: 401 Unauthorized
```

**Test token expiration:**
```bash
# Use the refresh token to get a new access token
# (First, you need to have saved your refresh token from login)
curl -X POST "$API_URL/api/auth/token/refresh/" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "<your-refresh-token-here>"
  }'

# Expected: New access and refresh tokens
```

---

## Database Testing

### Test 1: Access PostgreSQL Directly
```bash
# Connect to PostgreSQL pod
kubectl exec -it postgres-0 -n medilink -- psql -U medilink -d medilink_db

# Run some queries:
# List all tables:
\dt

# Count users:
SELECT COUNT(*) FROM auth_user;

# Count doctors:
SELECT COUNT(*) FROM doctors;

# See doctor working hours:
SELECT * FROM doctor_working_hours;

# See doctor time-off:
SELECT * FROM doctor_time_off;

# Exit:
\q
```

### Test 2: Check Migrations
```bash
# List migration jobs
kubectl get jobs -n medilink

# Expected: 7 completed jobs (one for each service + api-gateway)

# Check migration logs
kubectl logs job/auth-service-migration -n medilink
kubectl logs job/doctor-service-migration -n medilink

# Expected: "Operations to perform:", "Applying...", "OK"
```

---

## Performance Testing

### Test 1: Load Testing with Multiple Requests
```bash
# Create a simple load test script
cat > load_test.sh <<'EOF'
#!/bin/bash
API_URL=$(minikube service api-gateway-service -n medilink --url)
TOKEN="<your-token-here>"

echo "Running 50 concurrent requests..."
for i in {1..50}; do
  curl -s -X GET "$API_URL/api/doctors/" \
    -H "Authorization: Bearer $TOKEN" &
done
wait
echo "Done!"
EOF

chmod +x load_test.sh
./load_test.sh
```

### Test 2: Check Pod Resource Usage
```bash
# Check resource usage of all pods
kubectl top pods -n medilink

# Expected: CPU and memory usage for each pod
# Should be well within limits (256Mi-512Mi memory, 100m-500m CPU)
```

### Test 3: Test Pod Scaling
```bash
# Manually scale doctor-service to 5 replicas
kubectl scale deployment doctor-service -n medilink --replicas=5

# Wait and check
kubectl get pods -n medilink -l app=doctor-service

# Expected: 5 doctor-service pods

# Scale back to 3
kubectl scale deployment doctor-service -n medilink --replicas=3
```

---

## Full End-to-End Test Scenario

Here's a complete workflow test simulating a real-world scenario:

```bash
# 1. Register a doctor
curl -X POST "$API_URL/api/auth/register/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "dr_complete_test",
    "email": "complete@test.com",
    "password": "SecurePass123!",
    "password2": "SecurePass123!",
    "first_name": "Complete",
    "last_name": "Test",
    "role": "doctor"
  }'

# 2. Login and get token
RESPONSE=$(curl -s -X POST "$API_URL/api/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "dr_complete_test",
    "password": "SecurePass123!"
  }')

# Extract token (using jq if available, or manually copy)
export TEST_TOKEN=$(echo $RESPONSE | jq -r '.access')

# 3. Create doctor profile (user_id will be latest, e.g., 4)
curl -X POST "$API_URL/api/doctors/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TEST_TOKEN" \
  -d '{
    "user_id": 4,
    "specialty": "General Practice",
    "license_number": "MD99999"
  }'

# 4. Set up complete weekly schedule
for day in 1 2 3 4 5; do
  curl -X POST "$API_URL/api/doctors/4/working-hours/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TEST_TOKEN" \
    -d "{
      \"day_of_week\": $day,
      \"start_time\": \"08:00:00\",
      \"end_time\": \"17:00:00\"
    }"
done

# 5. Add lunch breaks for next 3 days
for i in 1 2 3; do
  DATE=$(date -d "+$i days" +%Y-%m-%d)
  curl -X POST "$API_URL/api/doctors/4/time-off/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TEST_TOKEN" \
    -d "{
      \"date\": \"$DATE\",
      \"start_time\": \"12:00:00\",
      \"end_time\": \"13:00:00\",
      \"reason\": \"Lunch\"
    }"
done

# 6. Check availability for tomorrow
TOMORROW=$(date -d "+1 day" +%Y-%m-%d)
curl -X GET "$API_URL/api/doctors/4/availability/?date=$TOMORROW&duration=30" \
  -H "Authorization: Bearer $TEST_TOKEN"

# 7. Verify the doctor profile
curl -X GET "$API_URL/api/doctors/4/" \
  -H "Authorization: Bearer $TEST_TOKEN"

# 8. Search for the doctor
curl -X GET "$API_URL/api/doctors/search/?specialty=General" \
  -H "Authorization: Bearer $TEST_TOKEN"
```

---

## Automated Testing Script

Run the automated test suite:

```bash
# Run the automated test script
chmod +x scripts/test-deployment.sh
./scripts/test-deployment.sh

# This will test:
# 1. Namespace exists
# 2. All pods running
# 3. All services exist
# 4. Database accessible
# 5. Auth service health
# 6. Doctor service health
# 7. API Gateway accessible
# 8. User registration
# 9. User login
# 10. Doctor profile creation
```

---

## Troubleshooting

### Problem: Pods Not Starting

**Check pod status:**
```bash
kubectl get pods -n medilink

# If pods are in CrashLoopBackOff or Error:
kubectl describe pod <pod-name> -n medilink
kubectl logs <pod-name> -n medilink
```

**Common fixes:**
```bash
# Restart a deployment
kubectl rollout restart deployment auth-service -n medilink

# Delete and recreate a pod
kubectl delete pod <pod-name> -n medilink
```

### Problem: Database Connection Issues

**Check database:**
```bash
# Check if postgres is running
kubectl get pods -n medilink -l app=postgres

# Check database logs
kubectl logs postgres-0 -n medilink

# Test connection
kubectl exec -it postgres-0 -n medilink -- psql -U medilink -d medilink_db -c "SELECT 1;"
```

**Fix:**
```bash
# Delete and recreate database
kubectl delete -f k8s/database/
kubectl apply -f k8s/database/
```

### Problem: Cannot Access API Gateway

**Get the correct URL:**
```bash
# Get API Gateway URL
minikube service api-gateway-service -n medilink --url

# Or use port forwarding
kubectl port-forward -n medilink service/api-gateway-service 8080:8000

# Then access: http://localhost:8080
```

### Problem: Migrations Not Running

**Manually run migrations:**
```bash
# For auth service
kubectl exec -it $(kubectl get pod -n medilink -l app=auth-service -o jsonpath="{.items[0].metadata.name}") -n medilink -- python manage.py migrate

# For doctor service
kubectl exec -it $(kubectl get pod -n medilink -l app=doctor-service -o jsonpath="{.items[0].metadata.name}") -n medilink -- python manage.py migrate
```

### Problem: 401 Unauthorized Errors

**Check token:**
```bash
# Verify token hasn't expired
# Tokens expire after 1 hour

# Get a new token by logging in again
curl -X POST "$API_URL/api/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "dr_smith",
    "password": "SecurePass123!"
  }'
```

### Problem: Inter-Service Communication Fails

**Check service DNS:**
```bash
# From inside a pod, test DNS resolution
kubectl exec -it $(kubectl get pod -n medilink -l app=doctor-service -o jsonpath="{.items[0].metadata.name}") -n medilink -- nslookup auth-service

# Test connectivity
kubectl exec -it $(kubectl get pod -n medilink -l app=doctor-service -o jsonpath="{.items[0].metadata.name}") -n medilink -- curl http://auth-service:8000/health/
```

### Problem: Out of Resources

**Check Minikube resources:**
```bash
# Check node resources
kubectl top nodes

# If low on resources, restart Minikube with more:
minikube stop
minikube delete
minikube start --cpus=4 --memory=8192 --disk-size=20g
```

---

## Clean Up

### Delete Everything
```bash
# Delete all resources
kubectl delete namespace medilink

# Stop Minikube
minikube stop

# Delete Minikube (if you want to start fresh)
minikube delete
```

### Partial Cleanup
```bash
# Delete just the services (keep database)
kubectl delete deployment --all -n medilink
kubectl delete service api-gateway-service -n medilink

# Delete just the database
kubectl delete -f k8s/database/
```

---

## Summary Checklist

After running all tests, you should have verified:

- [x] Infrastructure (29 pods running, 9 services)
- [x] Auth Service (register, login, profile, list users)
- [x] Doctor Service (CRUD operations on doctors, working hours, time-off)
- [x] Availability calculation (15-minute slots with conflict detection)
- [x] Inter-service communication (doctor service fetches user info)
- [x] Authentication and authorization (JWT tokens)
- [x] Database (PostgreSQL running, migrations applied)
- [x] API Gateway (routing to services)
- [x] Error handling (validation, unique constraints)
- [x] Performance (resource usage within limits)

---

## Next Steps

1. **Implement remaining services** to increase grade to A+
2. **Add comprehensive unit tests** (pytest)
3. **Add integration tests** (test inter-service flows)
4. **Set up CI/CD pipeline** (automated testing and deployment)
5. **Add monitoring** (Prometheus, Grafana)
6. **Add logging** (ELK stack or similar)
7. **Implement API documentation** (Swagger/OpenAPI)

---

**Need Help?**
- Check pod logs: `kubectl logs <pod-name> -n medilink`
- Check pod details: `kubectl describe pod <pod-name> -n medilink`
- Check service endpoints: `kubectl get endpoints -n medilink`
- Interactive shell: `kubectl exec -it <pod-name> -n medilink -- /bin/sh`

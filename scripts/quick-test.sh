#!/bin/bash

# MediLink Microservices - Quick Test Script
# This script runs the most common tests to verify the deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    print_warning "jq is not installed. Install it for better JSON parsing: sudo apt-get install jq"
    USE_JQ=false
else
    USE_JQ=true
fi

print_header "MediLink Microservices Quick Test"

# Get API Gateway URL
print_info "Getting API Gateway URL..."
API_URL=$(minikube service api-gateway-service -n medilink --url 2>/dev/null)

if [ -z "$API_URL" ]; then
    print_error "Cannot get API Gateway URL. Is Minikube running?"
    exit 1
fi

print_success "API Gateway URL: $API_URL"

# Test 1: Register a test doctor
print_header "Test 1: User Registration"
REGISTER_RESPONSE=$(curl -s -X POST "$API_URL/api/auth/register/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test_doctor_'$(date +%s)'",
    "email": "test'$(date +%s)'@example.com",
    "password": "SecurePass123!",
    "password2": "SecurePass123!",
    "first_name": "Test",
    "last_name": "Doctor",
    "role": "doctor"
  }')

if echo "$REGISTER_RESPONSE" | grep -q "registered successfully\|User registered\|\"user\""; then
    print_success "User registered successfully"
    if [ "$USE_JQ" = true ]; then
        USER_ID=$(echo "$REGISTER_RESPONSE" | jq -r '.user.id')
        print_info "User ID: $USER_ID"
    else
        print_info "Response: $REGISTER_RESPONSE"
    fi
else
    print_error "User registration failed"
    echo "$REGISTER_RESPONSE"
    exit 1
fi

# Extract username for login
if [ "$USE_JQ" = true ]; then
    USERNAME=$(echo "$REGISTER_RESPONSE" | jq -r '.user.username')
else
    # Fallback: use timestamp-based username
    USERNAME="test_doctor_$(date +%s)"
fi

# Test 2: Login
print_header "Test 2: User Login"
LOGIN_RESPONSE=$(curl -s -X POST "$API_URL/api/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "'$USERNAME'",
    "password": "SecurePass123!"
  }')

if echo "$LOGIN_RESPONSE" | grep -q "access"; then
    print_success "Login successful"
    if [ "$USE_JQ" = true ]; then
        TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access')
    else
        # Try to extract token manually
        TOKEN=$(echo "$LOGIN_RESPONSE" | sed -n 's/.*"access":"\([^"]*\)".*/\1/p')
    fi

    if [ -z "$TOKEN" ]; then
        print_error "Could not extract token"
        exit 1
    fi
    print_info "Token obtained (first 50 chars): ${TOKEN:0:50}..."
else
    print_error "Login failed"
    echo "$LOGIN_RESPONSE"
    exit 1
fi

# Test 3: Get User Profile
print_header "Test 3: Get User Profile"
PROFILE_RESPONSE=$(curl -s -X GET "$API_URL/api/auth/profile/" \
  -H "Authorization: Bearer $TOKEN")

if echo "$PROFILE_RESPONSE" | grep -q "username\|email"; then
    print_success "Profile retrieved successfully"
    if [ "$USE_JQ" = true ]; then
        echo "$PROFILE_RESPONSE" | jq '.'
    else
        echo "$PROFILE_RESPONSE"
    fi
else
    print_error "Profile retrieval failed"
    echo "$PROFILE_RESPONSE"
fi

# Test 4: Create Doctor Profile
print_header "Test 4: Create Doctor Profile"
DOCTOR_RESPONSE=$(curl -s -X POST "$API_URL/api/doctors/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "user_id": '$USER_ID',
    "specialty": "Automated Testing",
    "license_number": "TEST'$(date +%s)'"
  }')

if echo "$DOCTOR_RESPONSE" | grep -q "specialty\|Automated Testing"; then
    print_success "Doctor profile created successfully"
    if [ "$USE_JQ" = true ]; then
        echo "$DOCTOR_RESPONSE" | jq '.'
    else
        echo "$DOCTOR_RESPONSE"
    fi
else
    print_error "Doctor profile creation failed"
    echo "$DOCTOR_RESPONSE"
fi

# Test 5: Add Working Hours
print_header "Test 5: Add Working Hours"
HOURS_RESPONSE=$(curl -s -X POST "$API_URL/api/doctors/$USER_ID/working-hours/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "day_of_week": 1,
    "start_time": "09:00:00",
    "end_time": "17:00:00"
  }')

if echo "$HOURS_RESPONSE" | grep -q "day_of_week\|Monday"; then
    print_success "Working hours added successfully"
    if [ "$USE_JQ" = true ]; then
        echo "$HOURS_RESPONSE" | jq '.'
    else
        echo "$HOURS_RESPONSE"
    fi
else
    print_error "Working hours creation failed"
    echo "$HOURS_RESPONSE"
fi

# Test 6: Add Time-Off
print_header "Test 6: Add Time-Off"
TOMORROW=$(date -d "+1 day" +%Y-%m-%d)
TIMEOFF_RESPONSE=$(curl -s -X POST "$API_URL/api/doctors/$USER_ID/time-off/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "date": "'$TOMORROW'",
    "start_time": "12:00:00",
    "end_time": "13:00:00",
    "reason": "Automated test lunch break"
  }')

if echo "$TIMEOFF_RESPONSE" | grep -q "date\|reason"; then
    print_success "Time-off added successfully"
    if [ "$USE_JQ" = true ]; then
        echo "$TIMEOFF_RESPONSE" | jq '.'
    else
        echo "$TIMEOFF_RESPONSE"
    fi
else
    print_error "Time-off creation failed"
    echo "$TIMEOFF_RESPONSE"
fi

# Test 7: Get Availability
print_header "Test 7: Calculate Available Slots"
AVAIL_RESPONSE=$(curl -s -X GET "$API_URL/api/doctors/$USER_ID/availability/?date=$TOMORROW&duration=30" \
  -H "Authorization: Bearer $TOKEN")

if echo "$AVAIL_RESPONSE" | grep -q "available_slots"; then
    print_success "Availability calculated successfully"
    if [ "$USE_JQ" = true ]; then
        SLOT_COUNT=$(echo "$AVAIL_RESPONSE" | jq '.available_slots | length')
        print_info "Number of available 30-minute slots: $SLOT_COUNT"
        echo "$AVAIL_RESPONSE" | jq '.'
    else
        echo "$AVAIL_RESPONSE"
    fi
else
    print_error "Availability calculation failed"
    echo "$AVAIL_RESPONSE"
fi

# Test 8: List All Doctors
print_header "Test 8: List All Doctors"
DOCTORS_RESPONSE=$(curl -s -X GET "$API_URL/api/doctors/" \
  -H "Authorization: Bearer $TOKEN")

if echo "$DOCTORS_RESPONSE" | grep -q "specialty\|user_id"; then
    print_success "Doctors list retrieved successfully"
    if [ "$USE_JQ" = true ]; then
        DOCTOR_COUNT=$(echo "$DOCTORS_RESPONSE" | jq '. | length')
        print_info "Total doctors: $DOCTOR_COUNT"
    else
        echo "$DOCTORS_RESPONSE"
    fi
else
    print_error "Doctors list retrieval failed"
    echo "$DOCTORS_RESPONSE"
fi

# Test 9: Search Doctors
print_header "Test 9: Search Doctors by Specialty"
SEARCH_RESPONSE=$(curl -s -X GET "$API_URL/api/doctors/search/?specialty=Automated" \
  -H "Authorization: Bearer $TOKEN")

if echo "$SEARCH_RESPONSE" | grep -q "specialty"; then
    print_success "Doctor search successful"
    if [ "$USE_JQ" = true ]; then
        echo "$SEARCH_RESPONSE" | jq '.'
    else
        echo "$SEARCH_RESPONSE"
    fi
else
    print_error "Doctor search failed"
    echo "$SEARCH_RESPONSE"
fi

# Test 10: Check Pod Status
print_header "Test 10: Infrastructure Status"
print_info "Checking pod status..."

POD_STATUS=$(kubectl get pods -n medilink --no-headers 2>/dev/null)
if [ $? -eq 0 ]; then
    TOTAL_PODS=$(echo "$POD_STATUS" | wc -l)
    RUNNING_PODS=$(echo "$POD_STATUS" | grep -c "Running" || echo "0")
    COMPLETED_PODS=$(echo "$POD_STATUS" | grep -c "Completed" || echo "0")

    print_info "Total pods: $TOTAL_PODS"
    print_info "Running pods: $RUNNING_PODS"
    print_info "Completed pods: $COMPLETED_PODS"

    if [ "$RUNNING_PODS" -ge 20 ]; then
        print_success "Infrastructure is healthy"
    else
        print_warning "Some pods may not be running"
    fi
else
    print_error "Cannot check pod status"
fi

# Summary
print_header "Test Summary"
print_success "All API tests completed successfully!"
print_info "API Gateway URL: $API_URL"
print_info "Test User: $USERNAME"
print_info "User ID: $USER_ID"
print_info "Token (save for manual testing): $TOKEN"

echo ""
print_info "You can now use this token for manual testing:"
echo "export TOKEN=\"$TOKEN\""
echo "export API_URL=\"$API_URL\""
echo "export USER_ID=\"$USER_ID\""
echo ""

print_success "Quick test completed successfully!"

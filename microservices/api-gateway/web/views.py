"""
Web Interface Views for API Gateway
These views render HTML templates and make API calls to microservices
"""

import requests
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.views.decorators.http import require_http_methods
import json
from datetime import datetime, timedelta


# ============================================================================
# Helper Functions
# ============================================================================

def get_auth_headers(request):
    """Get authentication headers from session"""
    token = request.session.get('access_token')
    if token:
        return {'Authorization': f'Bearer {token}'}
    return {}


def is_authenticated(request):
    """Check if user is authenticated"""
    return 'access_token' in request.session and 'user' in request.session


def get_current_user(request):
    """Get current user from session"""
    return request.session.get('user', {})


# ============================================================================
# Authentication Views
# ============================================================================

@require_http_methods(["GET", "POST"])
def login_view(request):
    """Login page - renders form and handles authentication"""
    if request.method == 'GET':
        # If already logged in, redirect to appropriate home
        if is_authenticated(request):
            user = get_current_user(request)
            role = user.get('role', 'patient')
            if role == 'doctor':
                return redirect('doctor_home')
            elif role == 'pharmacy':
                return redirect('pharmacy_home')
            else:
                return redirect('patient_home')

        return render(request, 'accounts/login.html')

    # POST - handle login
    username = request.POST.get('username')
    password = request.POST.get('password')

    if not username or not password:
        messages.error(request, 'Please provide both username and password')
        return render(request, 'accounts/login.html')

    try:
        # Call auth service (API expects 'email' field)
        response = requests.post(
            f'{settings.AUTH_SERVICE_URL}/api/auth/login/',
            json={'email': username, 'password': password},
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()

            # Store tokens in session
            request.session['access_token'] = data['tokens']['access']
            request.session['refresh_token'] = data['tokens']['refresh']

            # Store user data from login response
            user_data = data['user']
            request.session['user'] = user_data

            # Redirect based on role
            role = user_data.get('role', 'patient')
            
            print(f"DEBUG: Login successful. Role: {role}")
            print(f"DEBUG: Request Host: {request.get_host()}")
            
            if role == 'doctor':
                return redirect('doctor_home')
            elif role == 'pharmacy':
                return redirect('pharmacy_home')
            else:
                return redirect('patient_home')
        else:
            # Handle error response
            try:
                error_data = response.json()
                error_msg = error_data.get('detail') or error_data.get('error') or error_data.get('message') or 'Invalid credentials'
            except:
                error_msg = f'Login failed with status {response.status_code}'
            
            messages.error(request, error_msg)
            return render(request, 'accounts/login.html')

    except requests.exceptions.RequestException as e:
        messages.error(request, f'Unable to connect to authentication service: {str(e)}')
        return render(request, 'accounts/login.html')
    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')
        return render(request, 'accounts/login.html')


@require_http_methods(["GET", "POST"])
def logout_view(request):
    """Logout - clear session"""
    request.session.flush()
    messages.success(request, 'You have been logged out successfully')
    return redirect('login')


@require_http_methods(["GET", "POST"])
def signup_step1_view(request):
    """Signup step 1 - choose role"""
    if request.method == 'GET':
        return render(request, 'accounts/signup_step1.html')

    # POST - store role and go to step 2
    user_type = request.POST.get('user_type')
    if user_type in ['patient', 'doctor', 'pharmacy']:
        request.session['signup_role'] = user_type
        return redirect('signup_step2')
    else:
        messages.error(request, 'Please select a valid account type')
        return render(request, 'accounts/signup_step1.html')


@require_http_methods(["GET", "POST"])
def signup_step2_view(request):
    """Signup step 2 - enter details"""
    role = request.session.get('signup_role')
    if not role:
        return redirect('signup_step1')

    if request.method == 'GET':
        return render(request, 'accounts/signup_step2.html', {'role': role})

    # POST - create account
    data = {
        'name': request.POST.get('name'),
        'email': request.POST.get('email'),
        'password': request.POST.get('password'),
        'password_confirm': request.POST.get('password_confirm'),
        'role': role
    }

    try:
        response = requests.post(
            f'{settings.AUTH_SERVICE_URL}/api/auth/register/',
            json=data,
            timeout=5
        )

        if response.status_code == 201:
            # Get tokens from registration response
            response_data = response.json()
            
            # Store tokens and user data in session
            if 'tokens' in response_data:
                request.session['access_token'] = response_data['tokens']['access']
                request.session['refresh_token'] = response_data['tokens']['refresh']
            
            if 'user' in response_data:
                request.session['user'] = response_data['user']
            
            # Clear signup role from session
            if 'signup_role' in request.session:
                del request.session['signup_role']
            
            messages.success(request, 'Account created successfully!')
            
            # Redirect based on role
            if role == 'doctor':
                return redirect('doctor_home')
            elif role == 'pharmacy':
                return redirect('pharmacy_home')
            else:
                return redirect('patient_home')
        else:
            error_data = response.json()
            for field, errors in error_data.items():
                if isinstance(errors, list):
                    messages.error(request, f'{field}: {errors[0]}')
                else:
                    messages.error(request, f'{field}: {errors}')
            return render(request, 'accounts/signup_step2.html', {'role': role})

    except requests.exceptions.RequestException as e:
        messages.error(request, f'Unable to connect to service: {str(e)}')
        return render(request, 'accounts/signup_step2.html', {'role': role})


# ============================================================================
# Doctor Views
# ============================================================================

@require_http_methods(["GET"])
def doctor_home_view(request):
    """Doctor home page - shows appointments and overview"""
    if not is_authenticated(request):
        return redirect('login')

    user = get_current_user(request)
    if user.get('role') != 'doctor':
        messages.error(request, 'Access denied: Doctor account required')
        return redirect('login')

    # Get doctor profile
    doctor_data = None
    try:
        doctor_response = requests.get(
            f'{settings.DOCTOR_SERVICE_URL}/api/doctors/{user["id"]}/',
            headers=get_auth_headers(request),
            timeout=5
        )
        if doctor_response.status_code == 200:
            doctor_data = doctor_response.json()
    except:
        pass

    # Fetch today's appointments from scheduling service
    appointments = []
    try:
        today = datetime.now().date()
        response = requests.get(
            f'{settings.SCHEDULING_SERVICE_URL}/api/appointments/',
            params={
                'doctor_id': user['id'],
                'date': today.isoformat(),
                'status': 'scheduled'
            },
            headers=get_auth_headers(request),
            timeout=5
        )
        
        if response.status_code == 200:
            appts = response.json()
            for appt in appts:
                # Fetch patient details
                try:
                    patient_response = requests.get(
                        f'{settings.AUTH_SERVICE_URL}/api/users/{appt["patient_id"]}/',
                        headers=get_auth_headers(request),
                        timeout=3
                    )
                    if patient_response.status_code == 200:
                        patient = patient_response.json()
                        appointments.append({
                            'id': appt['id'],
                            'name': f"{patient.get('first_name', '')} {patient.get('last_name', '')}",
                            'reason': appt.get('reason', 'Consultation'),
                            'time': appt.get('start_time', '').split(':')[0] + ':' + appt.get('start_time', '').split(':')[1] if appt.get('start_time') else 'N/A'
                        })
                except:
                    continue
    except:
        pass

    context = {
        'user': user,
        'doctor': doctor_data,
        'doctor_name': f"{user.get('first_name', '')} {user.get('last_name', '')}",
        'today': datetime.now().strftime('%B %d, %Y'),
        'appointments': appointments,
        'notifications': []
    }

    return render(request, 'accounts/doctor_home.html', context)


@require_http_methods(["GET"])
def doctor_appointments_view(request):
    """View doctor appointments"""
    if not is_authenticated(request):
        return redirect('login')

    user = get_current_user(request)
    if user.get('role') != 'doctor':
        messages.error(request, 'Access denied')
        return redirect('login')

    tab = request.GET.get('tab', 'upcoming')
    appointments = []
    
    try:
        # Fetch appointments from scheduling service
        params = {'doctor_id': user['id']}
        
        if tab == 'upcoming':
            params['status'] = 'scheduled'
            params['from_date'] = datetime.now().date().isoformat()
        elif tab == 'past':
            params['status'] = 'completed'
        elif tab == 'cancelled':
            params['status'] = 'cancelled'
        
        response = requests.get(
            f'{settings.SCHEDULING_SERVICE_URL}/api/appointments/',
            params=params,
            headers=get_auth_headers(request),
            timeout=5
        )
        
        if response.status_code == 200:
            appts = response.json()
            for appt in appts:
                # Fetch patient details
                try:
                    patient_response = requests.get(
                        f'{settings.AUTH_SERVICE_URL}/api/users/{appt["patient_id"]}/',
                        headers=get_auth_headers(request),
                        timeout=3
                    )
                    if patient_response.status_code == 200:
                        patient = patient_response.json()
                        appointments.append({
                            'id': appt['id'],
                            'patient_name': f"{patient.get('first_name', '')} {patient.get('last_name', '')}",
                            'patient_email': patient.get('email', ''),
                            'date': appt.get('appointment_date', ''),
                            'time': appt.get('start_time', ''),
                            'reason': appt.get('reason', 'Consultation'),
                            'status': appt.get('status', ''),
                            'notes': appt.get('notes', '')
                        })
                except:
                    continue
    except Exception as e:
        messages.error(request, f'Error loading appointments: {str(e)}')

    context = {
        'user': user,
        'appointments': appointments,
        'tab': tab
    }
    return render(request, 'accounts/doctor_appointments.html', context)


@require_http_methods(["GET", "POST"])
def doctor_new_appointment_view(request):
    """Create new appointment"""
    if not is_authenticated(request):
        return redirect('login')

    user = get_current_user(request)
    if user.get('role') != 'doctor':
        messages.error(request, 'Access denied')
        return redirect('login')

    if request.method == 'POST':
        # TODO: Implement appointment creation logic
        messages.info(request, 'Appointment creation not yet implemented')
        return redirect('doctor_appointments')

    context = {
        'user': user,
    }
    return render(request, 'accounts/doctor_new_appointment.html', context)


@require_http_methods(["GET"])
def doctor_full_schedule_view(request):
    """View full schedule"""
    if not is_authenticated(request):
        return redirect('login')

    user = get_current_user(request)
    if user.get('role') != 'doctor':
        messages.error(request, 'Access denied')
        return redirect('login')

    context = {
        'user': user,
        'schedule': [],  # TODO: Get from scheduling service
    }
    return render(request, 'accounts/doctor_full_schedule.html', context)


@require_http_methods(["GET"])
def doctor_patient_search_view(request):
    """Search patients"""
    if not is_authenticated(request):
        return redirect('login')

    user = get_current_user(request)
    if user.get('role') != 'doctor':
        messages.error(request, 'Access denied')
        return redirect('login')

    context = {
        'user': user,
        'patients': [],  # TODO: Get from patient service
    }
    return render(request, 'accounts/doctor_patients.html', context)


@require_http_methods(["GET", "POST"])
def doctor_add_patient_view(request):
    """Add new patient"""
    if not is_authenticated(request):
        return redirect('login')

    user = get_current_user(request)
    if user.get('role') != 'doctor':
        messages.error(request, 'Access denied')
        return redirect('login')

    if request.method == 'POST':
        messages.info(request, 'Add patient functionality not yet implemented')
        return redirect('doctor_patient_search')

    context = {
        'user': user,
    }
    return render(request, 'accounts/doctor_add_patient.html', context)


@require_http_methods(["GET"])
def doctor_appointment_detail_view(request, appointment_id):
    """View appointment details"""
    if not is_authenticated(request):
        return redirect('login')

    user = get_current_user(request)
    if user.get('role') != 'doctor':
        messages.error(request, 'Access denied')
        return redirect('login')

    context = {
        'user': user,
        'appointment': {'id': appointment_id},  # TODO: Get from scheduling service
    }
    return render(request, 'accounts/doctor_appointment_detail.html', context)


@require_http_methods(["GET", "POST"])
def doctor_appointment_edit_view(request, appointment_id):
    """Edit appointment"""
    if not is_authenticated(request):
        return redirect('login')

    user = get_current_user(request)
    if user.get('role') != 'doctor':
        messages.error(request, 'Access denied')
        return redirect('login')

    if request.method == 'POST':
        messages.info(request, 'Edit appointment functionality not yet implemented')
        return redirect('doctor_appointments')

    context = {
        'user': user,
        'appointment': {'id': appointment_id},  # TODO: Get from scheduling service
    }
    return render(request, 'accounts/doctor_appointment_edit.html', context)


@require_http_methods(["POST"])
def doctor_appointment_cancel_view(request, appointment_id):
    """Cancel appointment"""
    if not is_authenticated(request):
        return redirect('login')

    user = get_current_user(request)
    if user.get('role') != 'doctor':
        messages.error(request, 'Access denied')
        return redirect('login')

    messages.info(request, 'Cancel appointment functionality not yet implemented')
    return redirect('doctor_appointments')


@require_http_methods(["POST"])
def doctor_appointment_complete_view(request, appointment_id):
    """Mark appointment as complete"""
    if not is_authenticated(request):
        return redirect('login')

    user = get_current_user(request)
    if user.get('role') != 'doctor':
        messages.error(request, 'Access denied')
        return redirect('login')

    messages.info(request, 'Complete appointment functionality not yet implemented')
    return redirect('doctor_appointments')


@require_http_methods(["GET", "POST"])
def doctor_hours_view(request):
    """Doctor working hours management"""
    if not is_authenticated(request):
        return redirect('login')

    user = get_current_user(request)
    if user.get('role') != 'doctor':
        messages.error(request, 'Access denied')
        return redirect('login')

    if request.method == 'GET':
        # Get existing working hours
        working_hours = []
        try:
            response = requests.get(
                f'{settings.DOCTOR_SERVICE_URL}/api/doctors/{user["id"]}/working-hours/',
                headers=get_auth_headers(request),
                timeout=5
            )
            if response.status_code == 200:
                working_hours = response.json()
        except:
            pass

        context = {
            'user': user,
            'working_hours': working_hours,
            'days': [
                {'value': 1, 'name': 'Monday'},
                {'value': 2, 'name': 'Tuesday'},
                {'value': 3, 'name': 'Wednesday'},
                {'value': 4, 'name': 'Thursday'},
                {'value': 5, 'name': 'Friday'},
                {'value': 6, 'name': 'Saturday'},
                {'value': 7, 'name': 'Sunday'},
            ]
        }
        return render(request, 'accounts/doctor_hours.html', context)

    # POST - add/update working hours
    day_of_week = request.POST.get('day_of_week')
    start_time = request.POST.get('start_time')
    end_time = request.POST.get('end_time')

    try:
        response = requests.post(
            f'{settings.DOCTOR_SERVICE_URL}/api/doctors/{user["id"]}/working-hours/',
            json={
                'day_of_week': int(day_of_week),
                'start_time': start_time,
                'end_time': end_time
            },
            headers=get_auth_headers(request),
            timeout=5
        )

        if response.status_code == 201:
            messages.success(request, 'Working hours added successfully')
        else:
            error_data = response.json()
            messages.error(request, f'Error: {error_data}')

    except requests.exceptions.RequestException as e:
        messages.error(request, f'Unable to save working hours: {str(e)}')

    return redirect('doctor_hours')


@require_http_methods(["GET"])
def doctor_availability_view(request):
    """View doctor availability"""
    if not is_authenticated(request):
        return redirect('login')

    user = get_current_user(request)
    if user.get('role') != 'doctor':
        messages.error(request, 'Access denied')
        return redirect('login')

    # Get date and duration from query params
    date = request.GET.get('date')
    duration = request.GET.get('duration', '30')

    availability_data = None
    if date:
        try:
            response = requests.get(
                f'{settings.DOCTOR_SERVICE_URL}/api/doctors/{user["id"]}/availability/',
                params={'date': date, 'duration': duration},
                headers=get_auth_headers(request),
                timeout=5
            )
            if response.status_code == 200:
                availability_data = response.json()
        except:
            pass

    context = {
        'user': user,
        'date': date,
        'duration': duration,
        'availability': availability_data
    }

    return render(request, 'accounts/doctor_availability.html', context)


@require_http_methods(["GET"])
def view_doctor_availability_view(request):
    """View availability for a specific doctor (patient view)"""
    doctor_id = request.GET.get('doctor_id')
    date = request.GET.get('date')
    duration = request.GET.get('duration', '30')

    availability_data = None
    doctor_data = None

    if doctor_id and date:
        try:
            # Get doctor info
            doctor_response = requests.get(
                f'{settings.DOCTOR_SERVICE_URL}/api/doctors/{doctor_id}/',
                headers=get_auth_headers(request),
                timeout=5
            )
            if doctor_response.status_code == 200:
                doctor_data = doctor_response.json()

            # Get availability
            avail_response = requests.get(
                f'{settings.DOCTOR_SERVICE_URL}/api/doctors/{doctor_id}/availability/',
                params={'date': date, 'duration': duration},
                headers=get_auth_headers(request),
                timeout=5
            )
            if avail_response.status_code == 200:
                availability_data = avail_response.json()
        except:
            pass

    context = {
        'doctor': doctor_data,
        'date': date,
        'duration': duration,
        'availability': availability_data
    }

    return render(request, 'accounts/view_doctor_availability.html', context)


# ============================================================================
# Patient Views
# ============================================================================

@require_http_methods(["GET"])
def patient_home_view(request):
    """Patient home page"""
    if not is_authenticated(request):
        return redirect('login')

    user = get_current_user(request)
    if user.get('role') != 'patient':
        messages.error(request, 'Access denied: Patient account required')
        return redirect('login')

    context = {
        'user': user,
        'appointments': [],  # TODO: Get from scheduling service
        'prescriptions': [],  # TODO: Get from patient service
    }

    return render(request, 'accounts/patient_home.html', context)


@require_http_methods(["GET"])
def patient_search_doctors_view(request):
    """Search for doctors"""
    if not is_authenticated(request):
        return redirect('login')

    user = get_current_user(request)
    search = request.GET.get('search', '').strip()
    specialty = request.GET.get('specialty', '').strip()
    doctors = []

    try:
        # Get doctors from Doctor Service
        params = {}
        if specialty:
            params['specialty'] = specialty
        
        response = requests.get(
            f'{settings.DOCTOR_SERVICE_URL}/api/doctors/',
            params=params,
            headers=get_auth_headers(request),
            timeout=5
        )
        
        if response.status_code == 200:
            doctor_profiles = response.json()
            
            # Fetch user details from Auth Service for each doctor
            for profile in doctor_profiles:
                try:
                    user_response = requests.get(
                        f'{settings.AUTH_SERVICE_URL}/api/users/{profile["user_id"]}/',
                        headers=get_auth_headers(request),
                        timeout=5
                    )
                    if user_response.status_code == 200:
                        user_data = user_response.json()
                        doctor = {
                            'user_id': profile['user_id'],
                            'first_name': user_data.get('first_name', ''),
                            'last_name': user_data.get('last_name', ''),
                            'email': user_data.get('email', ''),
                            'phone': user_data.get('phone', ''),
                            'specialty': profile.get('specialty', ''),
                            'license_number': profile.get('license_number', ''),
                            'bio': f"Experienced {profile.get('specialty', 'medical')} specialist",
                            'consultation_fee': 100 + (profile['user_id'] * 20)  # Mock fee
                        }
                        
                        # Apply search filter
                        if search:
                            if (search.lower() in doctor['first_name'].lower() or 
                                search.lower() in doctor['last_name'].lower()):
                                doctors.append(doctor)
                        else:
                            doctors.append(doctor)
                except:
                    continue
    except Exception as e:
        messages.error(request, f'Error loading doctors: {str(e)}')

    context = {
        'user': user,
        'search': search,
        'specialty': specialty,
        'doctors': doctors
    }

    return render(request, 'accounts/patient_search_doctors.html', context)


@require_http_methods(["GET"])
def patient_appointments_view(request):
    """View patient appointments"""
    if not is_authenticated(request):
        return redirect('login')
    
    user = get_current_user(request)
    context = {'user': user, 'appointments': []}
    return render(request, 'accounts/patient_appointments.html', context)


@require_http_methods(["POST"])
def cancel_appointment_view(request, appointment_id):
    """Cancel appointment"""
    if not is_authenticated(request):
        return redirect('login')
    
    messages.success(request, 'Appointment cancelled successfully')
    return redirect('patient_home')


@require_http_methods(["GET"])
def patient_medical_history_view(request):
    """View medical history"""
    if not is_authenticated(request):
        return redirect('login')
    
    user = get_current_user(request)
    context = {'user': user, 'records': []}
    return render(request, 'accounts/patient_home.html', context)


@require_http_methods(["GET"])
def patient_prescriptions_view(request):
    """View prescriptions"""
    if not is_authenticated(request):
        return redirect('login')
    
    user = get_current_user(request)
    
    # TODO: Fetch prescriptions from appropriate service
    prescriptions = []
    
    context = {
        'user': user,
        'prescriptions': prescriptions
    }
    return render(request, 'accounts/view_prescriptions.html', context)


@require_http_methods(["GET"])
def browse_medicine_view(request):
    """Browse medicine catalog"""
    if not is_authenticated(request):
        return redirect('login')
    
    user = get_current_user(request)
    
    # TODO: Fetch medicines from inventory service
    medicines = []
    
    context = {
        'user': user,
        'medicines': medicines
    }
    return render(request, 'accounts/browse_medicine.html', context)


# ============================================================================
# Pharmacy Views
# ============================================================================

@require_http_methods(["GET"])
def pharmacy_home_view(request):
    """Pharmacy home page"""
    if not is_authenticated(request):
        return redirect('login')

    user = get_current_user(request)
    if user.get('role') != 'pharmacy':
        messages.error(request, 'Access denied: Pharmacy account required')
        return redirect('login')

    # Get pharmacy profile and staff from Pharmacy Service
    pharmacy_data = None
    staff = []
    pharmacy_name = user.get('username', 'Pharmacy')

    try:
        pharmacy_response = requests.get(
            f'{settings.PHARMACY_SERVICE_URL}/api/pharmacies/{user["id"]}/',
            headers=get_auth_headers(request),
            timeout=5
        )
        if pharmacy_response.status_code == 200:
            pharmacy_data = pharmacy_response.json()
            staff = pharmacy_data.get('staff', [])
            # Use user's first_name + last_name if available, else username
            if user.get('first_name'):
                pharmacy_name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
        elif pharmacy_response.status_code == 404:
            # Pharmacy profile doesn't exist yet, create it
            print(f"Pharmacy profile not found for user {user['id']}, will create if needed")
        else:
            print(f"Error fetching pharmacy profile: {pharmacy_response.status_code} - {pharmacy_response.text[:200]}")
    except Exception as e:
        print(f"Exception fetching pharmacy profile: {e}")
        pass

    # TODO: Get inventory statistics from Inventory Service when it's built
    # For now, use placeholder data
    # Get inventory statistics from Inventory Service
    total_medicines = 0
    total_stock = 0
    low_stock_count = 0
    expiring_count = 0
    critical_medicines = []

    try:
        # Get all stock for this pharmacy
        stock_response = requests.get(
            f'{settings.INVENTORY_SERVICE_URL}/api/inventory/stock/',
            params={'pharmacy': user['id']},
            headers=get_auth_headers(request),
            timeout=5
        )
        if stock_response.status_code == 200:
            stock_items = stock_response.json()
            total_medicines = len(stock_items)
            total_stock = sum(item.get('quantity', 0) for item in stock_items)

            from datetime import datetime, timedelta
            today = datetime.now().date()
            
            # Check for low stock and expiring items
            for item in stock_items:
                is_low_stock = item.get('quantity', 0) <= item.get('reorder_level', 10)
                is_expiring = False
                is_expired = False
                
                # Check expiry
                expiry_date = item.get('expiry_date')
                if expiry_date:
                    try:
                        exp_date = datetime.strptime(expiry_date, '%Y-%m-%d').date()
                        if exp_date < today:
                            is_expired = True
                            expiring_count += 1
                        elif exp_date <= today + timedelta(days=30):
                            is_expiring = True
                            expiring_count += 1
                    except:
                        pass
                
                if is_low_stock:
                    low_stock_count += 1
                    
                # Add to critical list if it meets any critical condition
                if (is_low_stock or is_expiring or is_expired) and len(critical_medicines) < 5:
                    # Add computed flags to the item
                    item['is_low_stock'] = is_low_stock
                    item['is_expiring'] = is_expiring
                    item['is_expired'] = is_expired
                    critical_medicines.append(item)
    except Exception as e:
        print(f"Error loading inventory stats: {e}")
        pass

    context = {
        'user': user,
        'pharmacy': pharmacy_data,
        'pharmacy_name': pharmacy_name,
        'staff': staff,
        'today': 'Today',
        'critical_medicines': critical_medicines,
        'total_medicines': total_medicines,
        'total_stock_quantity': total_stock,
        'low_stock_count': low_stock_count,
        'expiring_count': expiring_count,
    }

    return render(request, 'accounts/pharmacy_home.html', context)


@require_http_methods(["GET", "POST"])
def pharmacy_settings_view(request):
    """Pharmacy settings - manage profile and staff"""
    if not is_authenticated(request):
        return redirect('login')

    user = get_current_user(request)
    if user.get('role') != 'pharmacy':
        messages.error(request, 'Access denied')
        return redirect('login')

    # Get pharmacy profile from Pharmacy Service
    pharmacy_data = None
    staff = []
    pharmacy_name = user.get('username', 'Pharmacy')

    try:
        pharmacy_response = requests.get(
            f'{settings.PHARMACY_SERVICE_URL}/api/pharmacies/{user["id"]}/',
            headers=get_auth_headers(request),
            timeout=5
        )
        if pharmacy_response.status_code == 200:
            pharmacy_data = pharmacy_response.json()
            staff = pharmacy_data.get('staff', [])
            if user.get('first_name'):
                pharmacy_name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
        elif pharmacy_response.status_code == 404:
            print(f"Pharmacy profile not found for user {user['id']} in settings view")
        else:
            print(f"Error fetching pharmacy in settings: {pharmacy_response.status_code} - {pharmacy_response.text[:200]}")
    except Exception as e:
        print(f"Exception in settings pharmacy fetch: {e}")
        pass

    if request.method == 'POST':
        which_form = request.POST.get('which')

        if which_form == 'profile':
            # Update pharmacy profile
            address = request.POST.get('address')
            license_number = request.POST.get('license_number')
            phone = request.POST.get('phone')

            try:
                response = requests.put(
                    f'{settings.PHARMACY_SERVICE_URL}/api/pharmacies/{user["id"]}/',
                    json={
                        'user_id': user['id'],
                        'address': address,
                        'license_number': license_number,
                        'phone': phone
                    },
                    headers=get_auth_headers(request),
                    timeout=5
                )

                if response.status_code == 200:
                    messages.success(request, 'Pharmacy profile updated successfully')
                else:
                    try:
                        error_data = response.json()
                        messages.error(request, f'Error updating profile: {error_data}')
                    except ValueError:
                        messages.error(request, f'Error updating profile: Server returned {response.status_code}. Response: {response.text[:200]}')
            except requests.exceptions.RequestException as e:
                messages.error(request, f'Unable to update profile: {str(e)}')

            return redirect('pharmacy_settings')

        elif which_form == 'staff':
            # Add new staff member
            name = request.POST.get('name')
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            position = request.POST.get('position')

            try:
                response = requests.post(
                    f'{settings.PHARMACY_SERVICE_URL}/api/pharmacies/{user["id"]}/staff/',
                    json={
                        'pharmacy': user['id'],
                        'name': name,
                        'email': email,
                        'phone': phone,
                        'position': position
                    },
                    headers=get_auth_headers(request),
                    timeout=5
                )

                if response.status_code == 201:
                    messages.success(request, 'Staff member added successfully')
                else:
                    try:
                        error_data = response.json()
                        messages.error(request, f'Error adding staff: {error_data}')
                    except ValueError:
                        messages.error(request, f'Error adding staff: Server returned {response.status_code}. Response: {response.text[:200]}')
            except requests.exceptions.RequestException as e:
                messages.error(request, f'Unable to add staff: {str(e)}')

            return redirect('pharmacy_settings')

    context = {
        'user': user,
        'pharmacy': pharmacy_data,
        'pharmacy_name': pharmacy_name,
        'staff': staff,
    }

    return render(request, 'accounts/pharmacy_settings.html', context)


@require_http_methods(["POST"])
def delete_staff_view(request, staff_id):
    """Delete pharmacy staff member"""
    if not is_authenticated(request):
        return redirect('login')

    user = get_current_user(request)
    if user.get('role') != 'pharmacy':
        messages.error(request, 'Access denied')
        return redirect('login')

    try:
        response = requests.delete(
            f'{settings.PHARMACY_SERVICE_URL}/api/pharmacies/{user["id"]}/staff/{staff_id}/',
            headers=get_auth_headers(request),
            timeout=5
        )

        if response.status_code == 204:
            messages.success(request, 'Staff member deleted successfully')
        else:
            messages.error(request, 'Error deleting staff member')
    except requests.exceptions.RequestException as e:
        messages.error(request, f'Unable to delete staff: {str(e)}')

    return redirect('pharmacy_settings')


@require_http_methods(["POST"])
def delete_stock_view(request, stock_id):
    """Delete stock item"""
    if not is_authenticated(request):
        return redirect('login')

    user = get_current_user(request)
    if user.get('role') != 'pharmacy':
        messages.error(request, 'Access denied')
        return redirect('login')

    try:
        response = requests.delete(
            f'{settings.INVENTORY_SERVICE_URL}/api/inventory/stock/{stock_id}/',
            headers=get_auth_headers(request),
            timeout=5
        )

        if response.status_code == 204:
            messages.success(request, 'Stock item deleted successfully')
        else:
            messages.error(request, 'Error deleting stock item')
    except requests.exceptions.RequestException as e:
        messages.error(request, f'Unable to delete stock: {str(e)}')

    return redirect('view_inventory')


# Inventory views for pharmacy
@require_http_methods(["GET", "POST"])
def add_medicine_view(request):
    """Add medicine to inventory"""
    if not is_authenticated(request):
        return redirect('login')

    user = get_current_user(request)
    if user.get('role') != 'pharmacy':
        messages.error(request, 'Access denied')
        return redirect('login')

    if request.method == 'POST':
        # Get form data
        medicine_name = request.POST.get('medicine_name', '').strip()
        form = request.POST.get('form', '').strip()
        strength = request.POST.get('strength', '').strip()
        manufacturer = request.POST.get('manufacturer', '').strip()
        quantity = request.POST.get('quantity')
        price = request.POST.get('price')
        expiry_date = request.POST.get('expiry_date')
        reorder_level = request.POST.get('reorder_level', 10)
        batch_number = request.POST.get('batch_number', '')

        # Validation
        if not medicine_name or not form or not strength or not quantity or not price or not expiry_date:
            messages.error(request, 'Please fill in all required fields')
        else:
            try:
                # First, create or get the medicine in the catalog
                medicine_data = {
                    'name': medicine_name,
                    'form': form,
                    'strength': strength,
                    'manufacturer': manufacturer if manufacturer else '',
                    'generic_name': '',
                    'description': '',
                    'category': 'General',
                    'requires_prescription': False,
                    'base_price': float(price)
                }
                
                print(f"Creating medicine with data: {medicine_data}")
                medicine_response = requests.post(
                    f'{settings.INVENTORY_SERVICE_URL}/api/inventory/medicines/',
                    json=medicine_data,
                    headers=get_auth_headers(request),
                    timeout=5
                )
                
                print(f"Medicine creation response: {medicine_response.status_code}")
                print(f"Medicine creation response body: {medicine_response.text}")
                
                medicine_id = None
                if medicine_response.status_code == 201:
                    medicine_id = medicine_response.json().get('id')
                    print(f"Medicine created with ID: {medicine_id}")
                elif medicine_response.status_code == 400:
                    # Medicine might already exist, try to find it
                    print("Medicine creation failed, searching for existing...")
                    search_response = requests.get(
                        f'{settings.INVENTORY_SERVICE_URL}/api/inventory/medicines/',
                        params={'search': medicine_name},
                        headers=get_auth_headers(request),
                        timeout=5
                    )
                    if search_response.status_code == 200:
                        medicines = search_response.json()
                        print(f"Found {len(medicines)} medicines matching search")
                        # Find exact match
                        for med in medicines:
                            if (med.get('name', '').lower() == medicine_name.lower() and 
                                med.get('strength', '').lower() == strength.lower()):
                                medicine_id = med.get('id')
                                print(f"Found existing medicine with ID: {medicine_id}")
                                break
                
                if not medicine_id:
                    error_msg = f'Could not create or find medicine. API response: {medicine_response.text}'
                    print(error_msg)
                    messages.error(request, error_msg)
                else:
                    # Add stock to inventory service
                    stock_data = {
                        'pharmacy_id': user['id'],
                        'medicine': int(medicine_id),
                        'quantity': int(quantity),
                        'selling_price': float(price),
                        'expiry_date': expiry_date,
                        'reorder_level': int(reorder_level),
                        'batch_number': batch_number if batch_number else ''
                    }
                    
                    print(f"Adding stock with data: {stock_data}")
                    response = requests.post(
                        f'{settings.INVENTORY_SERVICE_URL}/api/inventory/stock/',
                        json=stock_data,
                        headers=get_auth_headers(request),
                        timeout=5
                    )

                    print(f"Stock creation response: {response.status_code}")
                    print(f"Stock creation response body: {response.text}")

                    if response.status_code == 201:
                        messages.success(request, 'Medicine added to inventory successfully')
                        return redirect('view_inventory')
                    else:
                        error_data = response.json() if response.content else {}
                        error_msg = error_data.get('detail', str(error_data))
                        messages.error(request, f'Error adding stock: {error_msg}')
            except requests.exceptions.RequestException as e:
                print(f"Request exception: {str(e)}")
                messages.error(request, f'Unable to add medicine: {str(e)}')

    # GET - show form
    context = {
        'user': user,
    }
    return render(request, 'accounts/add_medicine.html', context)


@require_http_methods(["GET", "POST"])
def update_stock_view(request):
    """Update stock quantity"""
    if not is_authenticated(request):
        return redirect('login')

    user = get_current_user(request)
    if user.get('role') != 'pharmacy':
        messages.error(request, 'Access denied')
        return redirect('login')

    if request.method == 'POST':
        # Get the ID of the stock item being updated from the submit button
        stock_id = request.POST.get('stock_id')
        
        if stock_id:
            quantity = request.POST.get(f'quantity_{stock_id}')
            price = request.POST.get(f'price_{stock_id}')
            expiry_date = request.POST.get(f'expiry_{stock_id}')

            try:
                # Prepare update data
                update_data = {}
                if quantity is not None:
                    update_data['quantity'] = int(quantity)
                if price is not None:
                    update_data['selling_price'] = float(price)
                if expiry_date:
                    update_data['expiry_date'] = expiry_date

                # Update stock via inventory service
                response = requests.patch(
                    f'{settings.INVENTORY_SERVICE_URL}/api/inventory/stock/{stock_id}/',
                    json=update_data,
                    headers=get_auth_headers(request),
                    timeout=5
                )

                if response.status_code == 200:
                    messages.success(request, 'Stock item updated successfully')
                else:
                    try:
                        error_data = response.json()
                        messages.error(request, f'Error updating stock: {error_data}')
                    except ValueError:
                        messages.error(request, f'Error updating stock: {response.status_code} - {response.text[:200]}')
            except requests.exceptions.RequestException as e:
                messages.error(request, f'Unable to update stock: {str(e)}')
            except ValueError:
                messages.error(request, 'Invalid input values')
        else:
            messages.error(request, 'No stock item selected')
            
        return redirect('update_stock')

    # GET - show stock items
    stock_items = []
    try:
        response = requests.get(
            f'{settings.INVENTORY_SERVICE_URL}/api/inventory/stock/',
            params={'pharmacy': user['id']},
            headers=get_auth_headers(request),
            timeout=5
        )
        if response.status_code == 200:
            stock_items = response.json()
        else:
            print(f"Error fetching stock items: {response.status_code} - {response.text[:200]}")
    except Exception as e:
        print(f"Exception fetching stock items: {e}")

    context = {
        'user': user,
        'stock_items': stock_items,
    }
    return render(request, 'accounts/update_stock.html', context)


@require_http_methods(["GET"])
def view_inventory_view(request):
    """View inventory"""
    if not is_authenticated(request):
        return redirect('login')

    user = get_current_user(request)
    if user.get('role') != 'pharmacy':
        messages.error(request, 'Access denied')
        return redirect('login')

    # Get filter parameters
    search_query = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '')
    sort_by = request.GET.get('sort', 'name')

    stock_items = []
    try:
        params = {'pharmacy': user['id']}

        response = requests.get(
            f'{settings.INVENTORY_SERVICE_URL}/api/inventory/stock/',
            params=params,
            headers=get_auth_headers(request),
            timeout=5
        )
        if response.status_code == 200:
            stock_items = response.json()

            # Apply search filter
            if search_query:
                stock_items = [
                    item for item in stock_items
                    if search_query.lower() in item.get('medicine', {}).get('name', '').lower()
                ]

            # Apply status filter
            from datetime import datetime, timedelta
            today = datetime.now().date()
            thirty_days = today + timedelta(days=30)

            for item in stock_items:
                # Add computed flags for template
                expiry_str = item.get('expiry_date', '')
                if expiry_str:
                    expiry_date = datetime.strptime(expiry_str, '%Y-%m-%d').date()
                    item['is_expired'] = expiry_date < today
                    item['is_expiring_soon'] = today <= expiry_date <= thirty_days
                else:
                    item['is_expired'] = False
                    item['is_expiring_soon'] = False
                
                item['is_low_stock'] = item.get('quantity', 0) <= item.get('reorder_level', 10)

            # Apply status filter
            if status_filter == 'low_stock':
                stock_items = [item for item in stock_items if item['is_low_stock']]
            elif status_filter == 'expiring':
                stock_items = [item for item in stock_items if item['is_expiring_soon']]
            elif status_filter == 'expired':
                stock_items = [item for item in stock_items if item['is_expired']]

            # Apply sorting
            if sort_by == 'name':
                stock_items.sort(key=lambda x: x.get('medicine', {}).get('name', '').lower())
            elif sort_by == '-name':
                stock_items.sort(key=lambda x: x.get('medicine', {}).get('name', '').lower(), reverse=True)
            elif sort_by == 'quantity':
                stock_items.sort(key=lambda x: x.get('quantity', 0))
            elif sort_by == '-quantity':
                stock_items.sort(key=lambda x: x.get('quantity', 0), reverse=True)
            elif sort_by == 'expiry_date':
                stock_items.sort(key=lambda x: x.get('expiry_date', '9999-12-31'))

    except Exception as e:
        messages.error(request, f'Error loading inventory: {str(e)}')

    context = {
        'user': user,
        'stock_items': stock_items,
        'search_query': search_query,
        'status_filter': status_filter,
        'sort_by': sort_by,
    }
    return render(request, 'accounts/view_inventory.html', context)


# ============================================================================
# Utility Views
# ============================================================================

@require_http_methods(["GET"])
def forgot_password_view(request):
    """Forgot password page"""
    return render(request, 'accounts/forgot_password.html')


@require_http_methods(["GET"])
def error_view(request):
    """Generic error page"""
    return render(request, 'accounts/error.html')

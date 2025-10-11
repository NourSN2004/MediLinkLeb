from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from django.utils import timezone
from .models import Appointment, Patient, Doctor, User
from .forms import SignupForm


def home_redirect(request):
    """Route users to appropriate homepage based on their role"""
    if request.user.is_authenticated:
        if hasattr(request.user, 'role'):
            if request.user.role == User.Role.DOCTOR:
                return redirect('doctor_home')
            elif request.user.role == User.Role.PATIENT:
                return redirect('patient_home')
            elif request.user.role == User.Role.PHARMACY:
                # You'll create this later for Sprint 2+
                return render(request, 'accounts/error.html', {
                    'message': 'Pharmacy dashboard coming soon!'
                })
        # If user has no role, send to login
        return redirect('login')
    return redirect('signup_step1')


def signup_step1(request):
    """
    Stores user_type in session and goes to step2.
    """
    if request.method == 'POST':
        user_type = request.POST.get('user_type')
        if user_type:
            request.session['user_type'] = user_type
            return redirect('signup_step2')
        messages.error(request, 'Please choose an account type.')
    return render(request, 'accounts/signup_step1.html')


def signup_step2(request):
    """
    Creates the user, logs them in, and shows 'verification sent'.
    """
    # Get user_type from session (set in step 1)
    user_type = request.session.get('user_type', 'patient')
    
    if request.method == 'POST':
        form = SignupForm(request.POST, user_type=user_type)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('verification_sent')
    else:
        form = SignupForm(user_type=user_type)
    
    return render(request, 'accounts/signup_step2.html', {'form': form})


def verification_sent(request):
    return render(request, 'accounts/verification_sent.html')


def custom_login(request):
    """Custom login view that redirects based on user role"""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                
                # Redirect based on role
                if hasattr(user, 'role'):
                    if user.role == User.Role.DOCTOR:
                        return redirect('doctor_home')
                    elif user.role == User.Role.PATIENT:
                        return redirect('patient_home')
                    elif user.role == User.Role.PHARMACY:
                        messages.info(request, 'Pharmacy dashboard coming soon!')
                        return redirect('login')
                
                # Default fallback
                return redirect('home_redirect')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'accounts/login.html', {'form': form, 'title': 'Sign in'})


@login_required
def doctor_home(request):
    """
    Renders the full-screen doctor dashboard.
    """
    today = timezone.localdate()
    
    # Check if user is actually a doctor
    if not hasattr(request.user, 'doctor'):
        return render(request, 'accounts/error.html', {
            'message': 'This page is for doctors only.'
        })
    
    # Get actual appointments for this doctor
    appointments_qs = Appointment.objects.filter(
        doctor=request.user.doctor,
        date_time__date=today,
        status=Appointment.Status.SCHEDULED
    ).select_related('patient__patient_id').order_by('date_time')
    
    # Format for template
    appointments = [
        {
            'name': appt.patient.patient_id.name,
            'time': appt.date_time.strftime('%I:%M %p'),
            'reason': appt.doctor_notes or 'General consultation'
        }
        for appt in appointments_qs
    ]
    
    return render(request, 'accounts/doctor_home.html', {
        'doctor_name': request.user.name or request.user.username,
        'today': today.strftime('%a, %b %d'),
        'appointments': appointments,
    })


def doctor_home_preview(request):
    """Unauthenticated preview of the doctor dashboard UI."""
    today = timezone.localdate().strftime('%a, %b %d')
    appointments = [
        {'name': 'Sara Habib', 'time': '09:00 AM', 'reason': 'Follow-up: Migraine'},
        {'name': 'Omar Nassar', 'time': '10:30 AM', 'reason': 'New visit: Chest pain'},
        {'name': 'Maya Karam', 'time': '01:15 PM', 'reason': 'Results review'},
    ]
    return render(request, 'accounts/doctor_home.html', {
        'doctor_name': 'Dr. Nour Shammaa',
        'today': today,
        'appointments': appointments,
    })


@login_required
def patient_home(request):
    """
    Patient Homepage view:
    - Shows upcoming appointments (today only)
    - Shows notifications counter
    - Provides sidebar navigation
    """
    user = request.user
    today = timezone.localdate()

    # Ensure this user is a patient
    if not hasattr(user, 'patient'):
        return render(request, "accounts/error.html", {
            "message": "This page is for patients only."
        })

    # Get today's appointments with doctor information
    today_appointments = Appointment.objects.filter(
        patient=user.patient,
        date_time__date=today,
        status=Appointment.Status.SCHEDULED
    ).select_related('doctor__doctor_id').order_by('date_time')

    # Mock notifications for now (replace with actual Notification model later)
    notifications = [
        {"message": "Your test results are ready.", "seen": False},
        {"message": "Dr. Leila confirmed your appointment for Oct 12.", "seen": True},
    ]
    unseen_count = sum(1 for n in notifications if not n["seen"])

    context = {
        "patient_name": user.name or user.username,
        "today": today.strftime("%A, %B %d"),
        "appointments": today_appointments,
        "unseen_count": unseen_count,
        "notifications": notifications,
    }

    return render(request, "accounts/patient_home.html", context)

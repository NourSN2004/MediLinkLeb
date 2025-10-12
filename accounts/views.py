from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from django.utils import timezone
from .models import Appointment, Patient, Doctor, User
from .services import AuthenticationService
from .forms import SignUpForm, LoginForm, ForgotPasswordForm, ResetPasswordForm


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
        if user_type in ['patient', 'doctor', 'pharmacy']:
            request.session['user_type'] = user_type
            return redirect('signup_step2')
        messages.error(request, 'Please choose an account type.')
    return render(request, 'accounts/signup_step1.html')


def signup_step2(request):
    """Step 2: Create user account"""
    user_type = request.session.get('user_type')
    if not user_type:
        messages.error(request, 'Please select an account type first.')
        return redirect('signup_step1')
    
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = AuthenticationService.signup_user(
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password1'],
                user_type=user_type,
                first_name=form.cleaned_data.get('first_name', ''),
                last_name=form.cleaned_data.get('last_name', '')
            )

            if user:
                login(request, user)
                AuthenticationService.send_verification_email(user)
                # Clear user_type from session
                request.session.pop('user_type', None)
                return redirect('verification_sent')
            else:
                messages.error(request, 'Error creating account. Please try again.')
    else:
        form = SignUpForm()

    return render(request, 'accounts/signup_step2.html', {'form': form})


def verification_sent(request):
    """Show verification email sent confirmation"""
    return render(request, 'accounts/verification_sent.html')

def verify_email(request, token):
    """Handle email verification (placeholder)"""
    # TODO: Implement actual verification logic with token stored in database
    messages.success(request, 'Email verified successfully!')
    return redirect('login')

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
    
    # Check if user is actually a doctor by role
    if request.user.role != User.Role.DOCTOR:
        return render(request, 'accounts/error.html', {
            'message': 'This page is for doctors only.'
        })
    
    # Get or create Doctor profile if it doesn't exist
    try:
        doctor_profile = request.user.doctor
    except Doctor.DoesNotExist:
        # Auto-create Doctor profile if user has doctor role but no profile
        doctor_profile = Doctor.objects.create(
            doctor_id=request.user,
            specialty='',
            license_number=''
        )
    
    # Get actual appointments for this doctor
    appointments_qs = Appointment.objects.filter(
        doctor=doctor_profile,
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
    """Unauthenticated preview of the doctor dashboard UI"""
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

    # Check if user is actually a patient by role
    if user.role != User.Role.PATIENT:
        return render(request, "accounts/error.html", {
            "message": "This page is for patients only."
        })

    # Get or create Patient profile if it doesn't exist
    try:
        patient_profile = user.patient
    except Patient.DoesNotExist:
        # Auto-create Patient profile if user has patient role but no profile
        patient_profile = Patient.objects.create(
            patient_id=user,
            national_id='',
            dob=None,
            gender='',
            blood_type='',
            history_summary=''
        )

    # Get today's appointments with doctor information
    today_appointments = Appointment.objects.filter(
        patient=patient_profile,
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


def forgot_password(request):
    """Handle forgot password request"""
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            success = AuthenticationService.initiate_password_reset(email)
            if success:
                messages.success(request, 'Password reset link has been sent to your email.')
                return redirect('login')
            else:
                messages.error(request, 'No account found with this email address.')
    else:
        form = ForgotPasswordForm()
    
    return render(request, 'accounts/forgot_password.html', {'form': form})


def reset_password(request, token):
    """Handle password reset with token"""
    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            success = AuthenticationService.reset_password(
                token,
                form.cleaned_data['password1']
            )
            if success:
                messages.success(request, 'Your password has been reset successfully. You can now sign in.')
                return redirect('login')
            else:
                messages.error(request, 'Invalid or expired reset link. Please request a new one.')
    else:
        form = ResetPasswordForm()
    
    return render(request, 'accounts/reset_password.html', {'form': form, 'token': token})
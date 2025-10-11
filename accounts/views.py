from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.utils import timezone

from .services import AuthenticationService
from .forms import SignUpForm, LoginForm, ForgotPasswordForm, ResetPasswordForm


def home_redirect(request):
    """Redirect to appropriate home page based on authentication status"""
    if request.user.is_authenticated:
        return redirect('doctor_home')
    return redirect('signup_step1')


def signup_step1(request):
    """Step 1: Select user type"""
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


def login_view(request):
    """Handle user login"""
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = AuthenticationService.login_user(
                form.cleaned_data['email'],
                form.cleaned_data['password']
            )
            if user:
                login(request, user)
                # Redirect based on user role
                if user.role == 'doctor':
                    return redirect('doctor_home')
                elif user.role == 'patient':
                    return redirect('patient_home')  # You'll need to create this
                elif user.role == 'pharmacy':
                    return redirect('pharmacy_home')  # You'll need to create this
                else:
                    return redirect('home_redirect')
            else:
                messages.error(request, 'Invalid email or password.')
    else:
        form = LoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})


def verification_sent(request):
    """Show verification email sent confirmation"""
    return render(request, 'accounts/verification_sent.html')


def verify_email(request, token):
    """Handle email verification (placeholder)"""
    # TODO: Implement actual verification logic with token stored in database
    messages.success(request, 'Email verified successfully!')
    return redirect('login')


@login_required
def doctor_home(request):
    """Render the doctor dashboard"""
    today = timezone.localdate()
    # TODO: Replace with actual database queries
    appointments = [
        {'name': 'Sara Habib', 'time': '09:00 AM', 'reason': 'Follow-up: Migraine'},
        {'name': 'Omar Nassar', 'time': '10:30 AM', 'reason': 'New visit: Chest pain'},
        {'name': 'Maya Karam', 'time': '01:15 PM', 'reason': 'Results review'},
    ]
    
    return render(request, 'accounts/doctor_home.html', {
        'doctor_name': request.user.name or request.user.email,
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

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.utils import timezone

from .forms import UserTypeForm, SignupForm

def home_redirect(request):
    # simple landing: send logged-in doctors to their home, everyone else to signup
    if request.user.is_authenticated:
        return redirect('doctor_home')
    return redirect('signup_step1')

def signup_step1(request):
    """
    Stores user_type in session and goes to step2.
    Your UI template handles the nice cards.
    """
    if request.method == 'POST':
        # If you are using plain radio inputs without Django form, read it directly:
        user_type = request.POST.get('user_type')
        if user_type:
            request.session['user_type'] = user_type
            return redirect('signup_step2')
        messages.error(request, 'Please choose an account type.')
    # render UI template (it already has the form markup)
    return render(request, 'accounts/signup_step1.html')

def signup_step2(request):
    """
    Creates the user, logs them in, and shows 'verification sent'.
    (Email sending is stubbed-you can plug Django email backend later.)
    """
    if request.method == 'POST':
        # If you use Django form objects in your template, uncomment the next line:
        # form = SignupForm(request.POST)
        # For your current template which renders {{ form.* }}, keep a form:
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            # here you would send verification email and mark 'inactive' if needed
            return redirect('verification_sent')
    else:
        form = SignupForm()

    return render(request, 'accounts/signup_step2.html', {'form': form})

def verification_sent(request):
    return render(request, 'accounts/verification_sent.html')

@login_required
def doctor_home(request):
    """
    Renders the full-screen doctor dashboard.
    Replace the mock appointments with your actual query.
    """
    today = timezone.localdate()
    appointments = [
        {'name': 'Sara Habib', 'time': '09:00 AM', 'reason': 'Follow-up: Migraine'},
        {'name': 'Omar Nassar', 'time': '10:30 AM', 'reason': 'New visit: Chest pain'},
        {'name': 'Maya Karam', 'time': '01:15 PM', 'reason': 'Results review'},
    ]
    return render(request, 'accounts/doctor_home.html', {
        'doctor_name': request.user.get_full_name() or request.user.username or 'Doctor',
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

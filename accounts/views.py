from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from django.utils import timezone
from .models import Appointment, Patient, Doctor, User, Pharmacy, Stock, Medicine, DoctorWorkingHours, DoctorTimeOff
from .services import AuthenticationService
from django.db.models import Q, Count, Sum, Prefetch
from datetime import timedelta
from django.db import transaction, IntegrityError
from .forms import SignUpForm, ForgotPasswordForm, ResetPasswordForm, MedicineForm, StockForm, NewMedicineStockForm, StockUpdateForm
from django.utils.dateparse import parse_date
from django.urls import reverse
from datetime import datetime, date
import logging
import calendar
from operator import attrgetter
from django.views.decorators.http import require_POST

from itertools import groupby


logger = logging.getLogger(__name__)

from datetime import time as datetime_time, timedelta as datetime_timedelta


def _snap_minutes(total: int, interval: int, direction: str) -> int:
    total = max(0, total)
    if direction == 'down':
        return total - (total % interval)
    remainder = total % interval
    if remainder:
        total += interval - remainder
    return total


def _round_time_component(value, interval: int = 15, direction: str = 'down') -> datetime_time:
    """Snap a time (str or datetime.time) to the nearest interval."""
    if isinstance(value, datetime_time):
        total = value.hour * 60 + value.minute
    else:
        hour, minute = map(int, str(value).split(':')[:2])
        total = hour * 60 + minute
    total = _snap_minutes(total, interval, direction)
    limit = 24 * 60 - interval
    total = max(0, min(total, limit))
    hour, minute = divmod(total, 60)
    return datetime_time(hour, minute)


def _round_dt(dt, interval: int = 15, direction: str = 'down'):
    total = dt.hour * 60 + dt.minute
    total = _snap_minutes(total, interval, direction)
    if direction == 'up' and total >= 24 * 60:
        return dt.replace(hour=0, minute=0, second=0, microsecond=0) + datetime_timedelta(days=1)
    total = max(0, min(total, 24 * 60 - interval))
    hour, minute = divmod(total, 60)
    return dt.replace(hour=hour, minute=minute, second=0, microsecond=0)



def _require_doctor(request):
    if request.user.role != User.Role.DOCTOR:
        return render(request, 'accounts/error.html', {
            'message': 'This page is for doctors only.'
        })
    return None


def _get_doctor_profile(user):
    try:
        return user.doctor
    except Doctor.DoesNotExist:
        return Doctor.objects.create(doctor_id=user, specialty='', license_number=None)


def _available_slots_for_date(doctor: Doctor, the_date: date):
    try:
        dow = the_date.weekday() + 1  # Python Mon=0 -> our enum Mon=1
        hours = DoctorWorkingHours.objects.get(doctor=doctor, day_of_week=dow)
    except DoctorWorkingHours.DoesNotExist:
        return None

    tz = timezone.get_current_timezone()
    start_dt = timezone.make_aware(datetime.combine(the_date, hours.start_time), tz)
    end_dt = timezone.make_aware(datetime.combine(the_date, hours.end_time), tz)

    start_dt = _round_dt(start_dt, 15, 'down')
    end_dt = _round_dt(end_dt, 15, 'up')

    if start_dt >= end_dt:
        return []

    slots = []
    current = start_dt
    while current < end_dt:
        slots.append(current.strftime('%H:%M'))
        current += timedelta(minutes=15)

    # Remove already booked times
    taken = set(
        Appointment.objects.filter(
            doctor=doctor,
            date_time__date=the_date,
            status=Appointment.Status.SCHEDULED,
        ).values_list('date_time__hour', 'date_time__minute')
    )
    free_slots = [s for s in slots if (int(s[:2]), int(s[3:5])) not in taken]

    # Remove personal time off blocks
    offs = DoctorTimeOff.objects.filter(doctor=doctor, date=the_date)
    if offs:
        pruned = []
        for s in free_slots:
            hh, mm = map(int, s.split(':'))
            slot_dt = timezone.make_aware(datetime(the_date.year, the_date.month, the_date.day, hh, mm), tz)
            blocked = False
            for off in offs:
                off_start = timezone.make_aware(datetime(the_date.year, the_date.month, the_date.day, off.start_time.hour, off.start_time.minute), tz)
                off_end = timezone.make_aware(datetime(the_date.year, the_date.month, the_date.day, off.end_time.hour, off.end_time.minute), tz)
                if off_start <= slot_dt < off_end:
                    blocked = True
                    break
            if not blocked:
                pruned.append(s)
        free_slots = pruned
    return free_slots

def home_redirect(request):
    """Route users to appropriate homepage based on their role"""
    if request.user.is_authenticated:
        if hasattr(request.user, 'role'):
            if request.user.role == User.Role.DOCTOR:
                return redirect('doctor_home')
            elif request.user.role == User.Role.PATIENT:
                return redirect('patient_home')
            elif request.user.role == User.Role.PHARMACY:
                return redirect('pharmacy_home')
        # If user has no role, send to login
        return redirect('login')
    return redirect('login')


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
                        return redirect('pharmacy_home')
                
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
    bad = _require_doctor(request)
    if bad:
        return bad
    
    # Get or create Doctor profile if it doesn't exist
    doctor_profile = _get_doctor_profile(request.user)
    
    # Get actual appointments for this doctor
    appointments_qs = Appointment.objects.filter(
        doctor=doctor_profile,
        date_time__date=today,
        status=Appointment.Status.SCHEDULED
    ).select_related('patient__patient_id').order_by('date_time')
    
    # Format for template
    appointments = [
        {
            'id': appt.id,
            'name': appt.patient.patient_id.name,
            'time': appt.date_time.strftime('%I:%M %p'),
            'reason': appt.doctor_notes or 'General consultation'
        }
        for appt in appointments_qs
    ]
    
    # Notifications: missed appointments (today, not completed/cancelled)
    now = timezone.now()
    missed_qs = Appointment.objects.filter(
        doctor=doctor_profile,
        date_time__date=today,
        date_time__lt=now,
        status=Appointment.Status.SCHEDULED,
    ).select_related('patient__patient_id').order_by('-date_time')
    notifications = [
        {
            'text': f"Missed: {a.patient.patient_id.name} at {timezone.localtime(a.date_time).strftime('%I:%M %p')}",
            'type': 'missed'
        }
        for a in missed_qs
    ]

    return render(request, 'accounts/doctor_home.html', {
        'doctor_name': request.user.name or request.user.username,
        'today': today.strftime('%a, %b %d'),
        'appointments': appointments,
        'notifications': notifications,
    })


@login_required
def doctor_appointments(request):
    bad = _require_doctor(request)
    if bad:
        return bad

    doctor = _get_doctor_profile(request.user)
    now = timezone.now()
    today = timezone.localdate()
    tab = request.GET.get('tab', 'today')

    if tab == 'past':
        qs = Appointment.objects.filter(
            doctor=doctor,
            date_time__lt=now,
        ).exclude(status=Appointment.Status.CANCELLED)
    elif tab == 'upcoming':
        qs = Appointment.objects.filter(
            doctor=doctor,
            date_time__gte=now,
            status=Appointment.Status.SCHEDULED,
        )
    else:  # today
        qs = Appointment.objects.filter(
            doctor=doctor,
            date_time__date=today,
        ).exclude(status=Appointment.Status.CANCELLED)

    qs = qs.select_related('patient__patient_id').order_by('date_time')

    appts = []
    tz = timezone.get_current_timezone()
    for a in qs:
        appts.append({
            'id': a.id,
            'patient_name': a.patient.patient_id.name,
            'patient_email': a.patient.patient_id.email,
            'datetime': timezone.localtime(a.date_time, tz).strftime('%a, %b %d %I:%M %p'),
            'status': a.status,
        })

    return render(request, 'accounts/doctor_appointments.html', {
        'appointments': appts,
        'tab': 'today' if tab == 'today' else ('past' if tab == 'past' else 'upcoming'),
    })


@login_required
def doctor_new_appointment(request):
    bad = _require_doctor(request)
    if bad:
        return bad

    doctor = _get_doctor_profile(request.user)

    if request.method == 'POST':
        date_str = request.POST.get('date')
        time_str = request.POST.get('time')
        patient_mode = request.POST.get('patient_mode', 'existing')
        notes = request.POST.get('notes', '').strip()

        if not date_str or not time_str:
            messages.error(request, 'Please choose a valid date and time.')
            return redirect('doctor_new_appointment')

        try:
            the_date = parse_date(date_str)
            hour, minute = map(int, time_str.split(':'))
            tz = timezone.get_current_timezone()
            dt = timezone.make_aware(datetime(the_date.year, the_date.month, the_date.day, hour, minute), tz)
        except Exception:
            messages.error(request, 'Invalid date or time format.')
            return redirect('doctor_new_appointment')

        # Resolve patient
        patient = None
        if patient_mode == 'existing':
            try:
                pid = int(request.POST.get('patient_id'))
                patient = Patient.objects.get(pk=pid)
            except (TypeError, ValueError, Patient.DoesNotExist):
                messages.error(request, 'Please select a valid patient.')
                return redirect('doctor_new_appointment')
        else:
            new_email = request.POST.get('new_email', '').strip()
            new_first = request.POST.get('new_first_name', '').strip()
            new_last = request.POST.get('new_last_name', '').strip()
            new_phone = request.POST.get('new_phone', '').strip()
            new_national_id = request.POST.get('new_national_id', '').strip()

            if not new_email:
                messages.error(request, 'Email is required for a new patient.')
                return redirect('doctor_new_appointment')

            if User.objects.filter(email=new_email).exists():
                messages.error(request, 'A user with this email already exists. Please select them as an existing patient.')
                return redirect('doctor_new_appointment')

            user = AuthenticationService.signup_user(
                email=new_email,
                password=User.objects.make_random_password(),
                user_type=User.Role.PATIENT,
                first_name=new_first,
                last_name=new_last,
            )
            if not user:
                messages.error(request, 'Could not create patient account.')
                return redirect('doctor_new_appointment')

            user.phone_number = new_phone
            user.save()
            patient = Patient.objects.create(patient_id=user, national_id=new_national_id)

        # Check within availability window and avoid collisions and time off
        avail_slots = _available_slots_for_date(doctor, dt.date())
        if avail_slots is not None:
            if dt.strftime('%H:%M') not in avail_slots:
                messages.error(request, 'Selected time is outside your availability or blocked.')
                return redirect('doctor_new_appointment')

        # Check for collisions
        if Appointment.objects.filter(doctor=doctor, date_time=dt, status=Appointment.Status.SCHEDULED).exists():
            messages.error(request, 'This time is already booked. Please choose another slot.')
            return redirect('doctor_new_appointment')

        try:
            Appointment.objects.create(
                doctor=doctor,
                patient=patient,
                date_time=dt,
                doctor_notes=notes,
                status=Appointment.Status.SCHEDULED,
            )
            messages.success(request, 'Appointment created.')
            return redirect(f"{reverse('doctor_appointments')}?tab=today")
        except Exception as e:
            logger.exception('Failed to create appointment')
            messages.error(request, f'Error creating appointment: {e}')
            return redirect('doctor_new_appointment')

    # GET
    q = request.GET.get('q', '').strip()
    patients = Patient.objects.all().select_related('patient_id')
    if q:
        patients = patients.filter(
            Q(patient_id__name__icontains=q) |
            Q(patient_id__email__icontains=q) |
            Q(patient_id__phone_number__icontains=q) |
            Q(national_id__icontains=q)
        )
    patients = patients.order_by('patient_id__name')

    selected_date = None
    available_slots = None
    date_q = request.GET.get('date')
    if date_q:
        try:
            selected_date = parse_date(date_q)
        except Exception:
            selected_date = None
        if selected_date:
            available_slots = _available_slots_for_date(doctor, selected_date)

    return render(request, 'accounts/doctor_new_appointment.html', {
        'patients': patients,
        'q': q,
        'selected_date': selected_date,
        'available_slots': available_slots,
    })


@login_required
def doctor_appointment_edit(request, appointment_id: int):
    bad = _require_doctor(request)
    if bad:
        return bad

    doctor = _get_doctor_profile(request.user)
    try:
        appt = Appointment.objects.select_related('patient__patient_id').get(id=appointment_id, doctor=doctor)
    except Appointment.DoesNotExist:
        messages.error(request, 'Appointment not found.')
        return redirect('doctor_appointments')

    if request.method == 'POST':
        date_str = request.POST.get('date')
        time_str = request.POST.get('time')
        notes = request.POST.get('notes', '').strip()
        patient_phone = request.POST.get('patient_phone', '').strip()

        try:
            the_date = parse_date(date_str)
            hour, minute = map(int, time_str.split(':'))
            tz = timezone.get_current_timezone()
            dt = timezone.make_aware(datetime(the_date.year, the_date.month, the_date.day, hour, minute), tz)
        except Exception:
            messages.error(request, 'Invalid date or time.')
            return redirect('doctor_appointment_edit', appointment_id=appointment_id)

        if Appointment.objects.filter(doctor=doctor, date_time=dt, status=Appointment.Status.SCHEDULED).exclude(id=appt.id).exists():
            messages.error(request, 'Selected time is already booked.')
            return redirect('doctor_appointment_edit', appointment_id=appointment_id)

        appt.date_time = dt
        appt.doctor_notes = notes
        # Update patient's phone number if provided
        if patient_phone:
            try:
                user = appt.patient.patient_id
                if user.phone_number != patient_phone:
                    user.phone_number = patient_phone
                    user.save(update_fields=['phone_number'])
            except Exception:
                logger.exception('Failed to update patient phone')
        appt.save()
        messages.success(request, 'Appointment updated.')
        return redirect('doctor_appointments')

    selected_date = appt.date_time.date()
    available_slots = _available_slots_for_date(doctor, selected_date)

    return render(request, 'accounts/doctor_appointment_edit.html', {
        'appointment': appt,
        'selected_date': selected_date,
        'available_slots': available_slots,
    })


@login_required
def doctor_appointment_cancel(request, appointment_id: int):
    bad = _require_doctor(request)
    if bad:
        return bad

    doctor = _get_doctor_profile(request.user)
    try:
        appt = Appointment.objects.get(id=appointment_id, doctor=doctor)
    except Appointment.DoesNotExist:
        messages.error(request, 'Appointment not found.')
        return redirect('doctor_appointments')

    if request.method == 'POST':
        appt.status = Appointment.Status.CANCELLED
        appt.save()
        messages.success(request, 'Appointment cancelled.')
    return redirect('doctor_appointments')


@login_required
def doctor_appointment_detail(request, appointment_id: int):
    bad = _require_doctor(request)
    if bad:
        return bad

    doctor = _get_doctor_profile(request.user)
    try:
        appt = Appointment.objects.select_related('patient__patient_id').get(id=appointment_id, doctor=doctor)
    except Appointment.DoesNotExist:
        messages.error(request, 'Appointment not found.')
        return redirect('doctor_appointments')

    return render(request, 'accounts/doctor_appointment_detail.html', {
        'appointment': appt,
    })


@login_required
def doctor_appointment_complete(request, appointment_id: int):
    bad = _require_doctor(request)
    if bad:
        return bad

    doctor = _get_doctor_profile(request.user)
    try:
        appt = Appointment.objects.get(id=appointment_id, doctor=doctor)
    except Appointment.DoesNotExist:
        messages.error(request, 'Appointment not found.')
        return redirect('doctor_appointments')

    if request.method == 'POST':
        appt.status = Appointment.Status.COMPLETED
        appt.save(update_fields=['status'])
        messages.success(request, 'Marked as done.')

    # Redirect back to where user came from if possible
    next_url = request.META.get('HTTP_REFERER') or reverse('doctor_appointments')
    return redirect(next_url)


@login_required
def doctor_patient_search(request):
    bad = _require_doctor(request)
    if bad:
        return bad

    doctor = _get_doctor_profile(request.user)
    q = (request.GET.get('q') or '').strip()
    results = []

    if q:
        # Find patients by name/email/phone/national id
        patients = Patient.objects.select_related('patient_id').filter(
            Q(patient_id__name__icontains=q) |
            Q(patient_id__email__icontains=q) |
            Q(patient_id__phone_number__icontains=q) |
            Q(national_id__icontains=q)
        ).order_by('patient_id__name')[:50]

        now = timezone.now()
        for p in patients:
            appts = Appointment.objects.filter(
                doctor=doctor,
                patient=p,
                status=Appointment.Status.SCHEDULED,
                date_time__gte=now,
            ).order_by('date_time')
            upcoming_count = appts.count()
            next_time = appts.first().date_time if upcoming_count else None
            results.append({
                'id': p.pk,
                'name': p.patient_id.name,
                'email': p.patient_id.email,
                'phone': p.patient_id.phone_number,
                'upcoming_count': upcoming_count,
                'next_time': timezone.localtime(next_time).strftime('%b %d, %I:%M %p') if next_time else None,
            })

    return render(request, 'accounts/patient_search.html', {
        'q': q,
        'results': results,
    })


@login_required
def doctor_full_schedule(request):
    bad = _require_doctor(request)
    if bad:
        return bad

    doctor = _get_doctor_profile(request.user)

    today = timezone.localdate()
    # Parse month/year or date
    sel_date = request.GET.get('date')
    year = request.GET.get('year')
    month = request.GET.get('month')

    if sel_date:
        try:
            selected_date = parse_date(sel_date) or today
        except Exception:
            selected_date = today
    else:
        try:
            selected_date = date(int(year), int(month), 1)
        except Exception:
            selected_date = date(today.year, today.month, 1)

    month_first = date(selected_date.year, selected_date.month, 1)
    _, month_days = calendar.monthrange(selected_date.year, selected_date.month)
    month_last = date(selected_date.year, selected_date.month, month_days)

    # Fetch all appts in month
    month_qs = Appointment.objects.filter(
        doctor=doctor,
        date_time__date__gte=month_first,
        date_time__date__lte=month_last,
    ).exclude(status=Appointment.Status.CANCELLED).select_related('patient__patient_id')

    # Group counts by date
    counts = {}
    times_by_date = {}
    for a in month_qs:
        d = a.date_time.date()
        counts[d] = counts.get(d, 0) + 1
        times_by_date.setdefault(d, []).append(timezone.localtime(a.date_time).strftime('%H:%M'))

    # Build calendar weeks (Mon..Sun)
    cal = calendar.Calendar(firstweekday=0)  # Monday
    weeks = []
    week = []
    for d in cal.itermonthdates(selected_date.year, selected_date.month):
        week.append({
            'date': d,
            'in_month': d.month == selected_date.month,
            'count': counts.get(d, 0),
            'times': ', '.join(sorted(times_by_date.get(d, []))) if d in times_by_date else '',
            'is_today': d == today,
            'is_selected': d == (parse_date(sel_date) if sel_date else today),
        })
        if len(week) == 7:
            weeks.append(week)
            week = []
    if week:
        weeks.append(week)

    # Determine selected day to show log
    show_date = parse_date(sel_date) if sel_date else today
    day_qs = Appointment.objects.filter(
        doctor=doctor,
        date_time__date=show_date,
    ).exclude(status=Appointment.Status.CANCELLED).select_related('patient__patient_id').order_by('date_time')

    day_appts = [
        {
            'id': a.id,
            'name': a.patient.patient_id.name,
            'email': a.patient.patient_id.email,
            'time': timezone.localtime(a.date_time).strftime('%I:%M %p'),
            'reason': a.doctor_notes or 'General consultation',
            'status': a.status,
        }
        for a in day_qs
    ]

    # Prev/next month
    prev_month = (month_first.replace(day=1) - timedelta(days=1)).replace(day=1)
    next_month = (month_last + timedelta(days=1)).replace(day=1)

    ctx = {
        'year': selected_date.year,
        'month': selected_date.month,
        'month_name': month_first.strftime('%B'),
        'weeks': weeks,
        'selected_date': show_date,
        'day_appts': day_appts,
        'prev_year': prev_month.year,
        'prev_month': prev_month.month,
        'next_year': next_month.year,
        'next_month': next_month.month,
    }
    return render(request, 'accounts/doctor_full_schedule.html', ctx)


@login_required
def doctor_hours(request):
    bad = _require_doctor(request)
    if bad:
        return bad

    doctor = _get_doctor_profile(request.user)
    today = timezone.localdate()

    if request.method == 'POST':
        form_kind = request.POST.get('form', 'hours')

        if form_kind == 'hours':
            # Save weekly hours
            for num, name in DoctorWorkingHours.DayOfWeek.choices:
                active = request.POST.get(f'active_{num}')
                start = request.POST.get(f'start_{num}')
                end = request.POST.get(f'end_{num}')

                # remove if not active or missing times
                if not active or not start or not end:
                    DoctorWorkingHours.objects.filter(doctor=doctor, day_of_week=num).delete()
                    continue

                # Validate order
                try:
                    sh, sm = map(int, start.split(':'))
                    eh, em = map(int, end.split(':'))
                    if (eh, em) <= (sh, sm):
                        messages.error(request, f"{name}: End time must be after start time.")
                        continue
                except Exception:
                    messages.error(request, f"{name}: Invalid time format.")
                    continue

                start = _round_time_component(start, 15, 'down')
                end = _round_time_component(end, 15, 'up')

                # create/update
                DoctorWorkingHours.objects.update_or_create(
                    doctor=doctor,
                    day_of_week=num,
                    defaults={'start_time': start, 'end_time': end}
                )

            messages.success(request, 'Availability saved.')
            return redirect('doctor_hours')

        elif form_kind == 'timeoff':
            date_str = request.POST.get('to_date')
            start = request.POST.get('to_start')
            end = request.POST.get('to_end')
            reason = request.POST.get('to_reason', '').strip()
            try:
                d = parse_date(date_str)
                if not d or not start or not end:
                    raise ValueError('Please fill date, start and end')
                start_time = _round_time_component(start, 15, 'down')
                end_time = _round_time_component(end, 15, 'up')
                if end_time <= start_time:
                    raise ValueError('End time must be after start time')
                DoctorTimeOff.objects.create(doctor=doctor, date=d, start_time=start_time, end_time=end_time, reason=reason)
                messages.success(request, 'Time off added.')
            except Exception as e:
                messages.error(request, f'Could not add time off: {e}')
            return redirect('doctor_hours')

        elif form_kind == 'delete_timeoff':
            try:
                tid = int(request.POST.get('to_id'))
                DoctorTimeOff.objects.filter(id=tid, doctor=doctor).delete()
                messages.success(request, 'Time off removed.')
            except Exception:
                messages.error(request, 'Could not remove time off.')
            return redirect('doctor_hours')

    # GET
    # Build weekly days state
    days = []
    existing = {h.day_of_week: h for h in DoctorWorkingHours.objects.filter(doctor=doctor)}
    for num, name in DoctorWorkingHours.DayOfWeek.choices:
        h = existing.get(num)
        days.append({
            'num': num,
            'name': name,
            'active': bool(h),
            'start': h.start_time.strftime('%H:%M') if h else '',
            'end': h.end_time.strftime('%H:%M') if h else '',
        })

    timeoffs = DoctorTimeOff.objects.filter(doctor=doctor, date__gte=today).order_by('date', 'start_time')
    return render(request, 'accounts/doctor_hours.html', {
        'days': days,
        'timeoffs': timeoffs,
        'today': today,
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
    - Shows upcoming and past appointments
    - Displays notifications counter
    - Provides sidebar navigation
    """
    user = request.user
    today = timezone.localdate()
    now = timezone.now()

    # Ensure user is actually a patient
    if user.role != User.Role.PATIENT:
        return render(request, "accounts/error.html", {
            "message": "This page is for patients only."
        })

    # Get or create Patient profile if it doesn't exist
    try:
        patient_profile = user.patient
    except Patient.DoesNotExist:
        patient_profile = Patient.objects.create(
            patient_id=user,
            national_id='',
            dob=None,
            gender='',
            blood_type='',
            history_summary=''
        )

    # ✅ Upcoming appointments (including today)
    upcoming_appointments = Appointment.objects.filter(
        patient=patient_profile,
        date_time__gte=now,
        status=Appointment.Status.SCHEDULED
    ).select_related('doctor__doctor_id').order_by('date_time')

    # ✅ Past appointments (not cancelled)
    past_appointments = Appointment.objects.filter(
        patient=patient_profile,
        date_time__lt=now
    ).exclude(status=Appointment.Status.CANCELLED).select_related('doctor__doctor_id').order_by('-date_time')

    # Mock notifications (replace later with real model)
    notifications = [
        {"message": "Your test results are ready.", "seen": False},
        {"message": "Dr. Leila confirmed your appointment for Oct 12.", "seen": True},
    ]
    unseen_count = sum(1 for n in notifications if not n["seen"])

    # ✅ Only one tiny addition below ↓ (no logic changes)
    context = {
        "patient_name": user.name or user.username,
        "today": today.strftime("%A, %B %d"),
        "appointments": upcoming_appointments,  # <-- added for template compatibility
        "upcoming_appointments": upcoming_appointments,
        "past_appointments": past_appointments,
        "unseen_count": unseen_count,
        "notifications": notifications,
    }

    return render(request, "accounts/patient_home.html", context)


@login_required
def pharmacy_home(request):
    """
    Renders the pharmacy dashboard with inventory management features.
    Shows inventory summary, critical medicines, and quick actions.
    """
    # Ensure user is a pharmacy
    if request.user.role != User.Role.PHARMACY:
        return render(request, 'accounts/error.html', {
            'message': 'This page is for pharmacies only.'
        })
    
    try:
        pharmacy = request.user.pharmacy
    except Pharmacy.DoesNotExist:
        # Auto-create Pharmacy profile if user has pharmacy role but no profile
        pharmacy = Pharmacy.objects.create(
            pharmacy_id=request.user,
            license_number=None,
            address=''
        )
    
    today = timezone.localdate()
    
    # Get all stocks for this pharmacy
    stocks = Stock.objects.filter(pharmacy=pharmacy).select_related('medicine')
    
    # Calculate inventory metrics
    total_medicines = stocks.values('medicine').distinct().count()
    total_stock_quantity = stocks.aggregate(total=Sum('quantity'))['total'] or 0
    
    # Low stock threshold (you can make this configurable)
    LOW_STOCK_THRESHOLD = 10
    low_stock_count = stocks.filter(quantity__lte=LOW_STOCK_THRESHOLD).values('medicine').distinct().count()
    
    # Expiry alerts - expired or expiring within 30 days
    expiry_threshold = today + timedelta(days=30)
    expiring_stocks = stocks.filter(
        Q(expiry_date__lte=expiry_threshold) & Q(expiry_date__gte=today)
    ).values('medicine').distinct().count()
    
    expired_count = stocks.filter(expiry_date__lt=today).values('medicine').distinct().count()
    
    # Critical medicines list - combine low stock and expiring/expired
    critical_medicines = []
    
    # Get medicines with low stock or expiring soon
    critical_stock_ids = stocks.filter(
        Q(quantity__lte=LOW_STOCK_THRESHOLD) | 
        Q(expiry_date__lte=expiry_threshold)
    ).order_by('expiry_date', 'quantity')
    
    seen_medicines = set()
    for stock in critical_stock_ids:
        if stock.medicine.id not in seen_medicines:
            seen_medicines.add(stock.medicine.id)
            
            # Determine status
            status = 'ok'
            status_text = 'In Stock'
            
            if stock.expiry_date < today:
                status = 'expired'
                status_text = 'Expired'
            elif stock.expiry_date <= expiry_threshold:
                status = 'expiring'
                status_text = 'Expiring Soon'
            elif stock.quantity <= LOW_STOCK_THRESHOLD:
                status = 'low'
                status_text = 'Low Stock'
            
            critical_medicines.append({
                'id': stock.id,
                'name': stock.medicine.name,
                'strength': stock.medicine.strength,
                'form': stock.medicine.dosage_form,
                'quantity': stock.quantity,
                'expiry_date': stock.expiry_date,
                'status': status,
                'status_text': status_text,
                'price': stock.price,
            })
    
    # Limit to top 10 most critical
    critical_medicines = critical_medicines[:10]
    
    context = {
        'pharmacy_name': pharmacy.pharmacy_id.name,
        'pharmacist_name': 'Ahmad Yateem',
        'today': today.strftime('%A, %B %d, %Y'),
        'total_medicines': total_medicines,
        'total_stock_quantity': total_stock_quantity,
        'low_stock_count': low_stock_count,
        'expiring_count': expiring_stocks,
        'expired_count': expired_count,
        'critical_medicines': critical_medicines,
        'has_inventory': total_medicines > 0,
    }
    
    return render(request, 'accounts/pharmacy_home.html', context)


def pharmacy_home_preview(request):
    """
    Unauthenticated preview of the pharmacy dashboard UI.
    Shows demo data to showcase the pharmacy homepage features.
    """
    from datetime import date
    
    today = date.today()
    
    # Demo critical medicines
    demo_medicines = [
        {
            'id': 1,
            'name': 'Paracetamol',
            'strength': '500mg',
            'form': 'Tablet',
            'quantity': 8,
            'expiry_date': today + timedelta(days=90),
            'status': 'low',
            'status_text': 'Low Stock',
            'price': '2.50',
        },
        {
            'id': 2,
            'name': 'Amoxicillin',
            'strength': '250mg',
            'form': 'Capsule',
            'quantity': 45,
            'expiry_date': today + timedelta(days=25),
            'status': 'expiring',
            'status_text': 'Expiring Soon',
            'price': '12.50',
        },
        {
            'id': 3,
            'name': 'Ibuprofen',
            'strength': '400mg',
            'form': 'Tablet',
            'quantity': 25,
            'expiry_date': today - timedelta(days=10),
            'status': 'expired',
            'status_text': 'Expired',
            'price': '3.75',
        },
        {
            'id': 4,
            'name': 'Omeprazole',
            'strength': '20mg',
            'form': 'Capsule',
            'quantity': 6,
            'expiry_date': today + timedelta(days=120),
            'status': 'low',
            'status_text': 'Low Stock',
            'price': '8.25',
        },
        {
            'id': 5,
            'name': 'Metformin',
            'strength': '500mg',
            'form': 'Tablet',
            'quantity': 4,
            'expiry_date': today + timedelta(days=15),
            'status': 'expiring',
            'status_text': 'Expiring Soon',
            'price': '4.50',
        },
    ]
    
    context = {
        'pharmacy_name': 'GreenLife Pharmacy (Demo)',
        'pharmacist_name': 'Ahmad Yateem',
        'today': today.strftime('%A, %B %d, %Y'),
        'total_medicines': 15,
        'total_stock_quantity': 674,
        'low_stock_count': 5,
        'expiring_count': 4,
        'expired_count': 2,
        'critical_medicines': demo_medicines,
        'has_inventory': True,
    }
    
    return render(request, 'accounts/pharmacy_home.html', context)


# ============================================================================
# ADMIN/UTILITY ACTIONS
# ============================================================================

@login_required
@require_POST
def populate_pharmacies(request):
    """Populate demo medicines and stock for all pharmacy accounts.

    Restricted to superusers to avoid accidental mass writes.
    """
    if not request.user.is_superuser:
        return render(request, 'accounts/error.html', {
            'message': 'This action is restricted to administrators.'
        })

    try:
        from populate_pharmacy import populate as populate_all
        populate_all()
        messages.success(request, 'Pharmacy demo data populated successfully.')
    except Exception as exc:
        messages.error(request, f'Population failed: {exc}')
    # Return user to pharmacy dashboard or home
    return redirect('pharmacy_home')

# ============================================================================
# PHARMACY MEDICINE MANAGEMENT VIEWS
# ============================================================================

@login_required
def add_medicine(request):
    """Add a new medicine to the catalog with stock."""
    # Ensure user is a pharmacy
    if request.user.role != User.Role.PHARMACY:
        return render(request, 'accounts/error.html', {
            'message': 'This page is for pharmacies only.'
        })
    
    try:
        pharmacy = request.user.pharmacy
    except Pharmacy.DoesNotExist:
        pharmacy = Pharmacy.objects.create(
            pharmacy_id=request.user,
            license_number=None,
            address=''
        )
    
    if request.method == 'POST':
        medicine_form = MedicineForm(request.POST)
        stock_form = NewMedicineStockForm(request.POST)
        
        # Debug logging
        print(f"POST data: {request.POST}")
        print(f"Medicine form valid: {medicine_form.is_valid()}")
        print(f"Stock form valid: {stock_form.is_valid()}")
        
        if medicine_form.is_valid() and stock_form.is_valid():
            try:
                with transaction.atomic():
                    # Get cleaned data
                    name = medicine_form.cleaned_data['name']
                    strength = medicine_form.cleaned_data['strength']
                    dosage_form = medicine_form.cleaned_data['dosage_form']
                    description = medicine_form.cleaned_data.get('description', '')
                    
                    # Get or create medicine
                    medicine, created = Medicine.objects.get_or_create(
                        name=name,
                        strength=strength,
                        dosage_form=dosage_form,
                        defaults={'description': description}
                    )
                    
                    print(f"Medicine {'created' if created else 'found'}: {medicine}")
                    
                    # Get stock data
                    quantity = stock_form.cleaned_data['quantity']
                    price = stock_form.cleaned_data['price']
                    expiry_date = stock_form.cleaned_data['expiry_date']
                    
                    # Check for existing stock with same expiry
                    existing_stock = Stock.objects.filter(
                        pharmacy=pharmacy,
                        medicine=medicine,
                        expiry_date=expiry_date
                    ).first()
                    
                    if existing_stock:
                        # Update existing stock
                        existing_stock.quantity += quantity
                        existing_stock.price = price
                        existing_stock.save()
                        print(f"Updated stock: {existing_stock}")
                        messages.success(request, f'✓ Updated stock for {medicine.name}!')
                    else:
                        # Create new stock
                        stock = Stock.objects.create(
                            pharmacy=pharmacy,
                            medicine=medicine,
                            quantity=quantity,
                            price=price,
                            expiry_date=expiry_date
                        )
                        print(f"Created stock: {stock}")
                        messages.success(request, f'✓ Successfully added {medicine.name} to inventory!')
                    
                    return redirect('pharmacy_home')
                    
            except IntegrityError as e:
                print(f'IntegrityError: {e}')
                messages.error(request, 'This medicine/stock combination already exists.')
            except Exception as e:
                print(f'Exception: {e}')
                import traceback
                traceback.print_exc()
                messages.error(request, f'Error: {str(e)}')
        else:
            # Form validation errors
            print(f"Medicine form errors: {medicine_form.errors}")
            print(f"Stock form errors: {stock_form.errors}")
            
            for field, errors in medicine_form.errors.items():
                for error in errors:
                    messages.error(request, f'Medicine {field}: {error}')
            for field, errors in stock_form.errors.items():
                for error in errors:
                    messages.error(request, f'Stock {field}: {error}')
    else:
        medicine_form = MedicineForm()
        stock_form = NewMedicineStockForm()
    
    context = {
        'medicine_form': medicine_form,
        'stock_form': stock_form,
        'pharmacy': pharmacy,
        'pharmacy_name': pharmacy.pharmacy_id.name,
        'pharmacist_name': 'Ahmad Yateem',
    }
    
    return render(request, 'accounts/add_medicine.html', context)

from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages

@login_required
def cancel_appointment(request, appt_id):
    """
    Allows a patient to cancel their own appointment.
    """
    user = request.user
    if user.role != User.Role.PATIENT:
        return render(request, "accounts/error.html", {
            "message": "Unauthorized access."
        })

    appointment = get_object_or_404(Appointment, id=appt_id, patient=user.patient)

    if request.method == "POST":
        appointment.status = Appointment.Status.CANCELLED
        appointment.save()
        messages.success(request, "Your appointment was cancelled successfully.")
        return redirect("patient_home")

    return render(request, "accounts/error.html", {
        "message": "Invalid request method."
    })

@login_required
def update_stock(request):
    """View and update stock levels for all medicines."""
    if request.user.role != User.Role.PHARMACY:
        return render(request, 'accounts/error.html', {
            'message': 'This page is for pharmacies only.'
        })
    
    try:
        pharmacy = request.user.pharmacy
    except Pharmacy.DoesNotExist:
        pharmacy = Pharmacy.objects.create(
            pharmacy_id=request.user,
            license_number=None,
            address=''
        )
    
    stocks = Stock.objects.filter(pharmacy=pharmacy).select_related('medicine').order_by('medicine__name')
    all_medicines = Medicine.objects.all().order_by('name')
    
    if request.method == 'POST':
        print(f"Update stock POST: {request.POST}")
        updated_count = 0
        
        try:
            with transaction.atomic():
                for stock in stocks:
                    quantity_key = f'quantity_{stock.id}'
                    price_key = f'price_{stock.id}'
                    expiry_key = f'expiry_{stock.id}'
                    
                    if quantity_key in request.POST:
                        try:
                            new_quantity = int(request.POST[quantity_key])
                            new_price = float(request.POST[price_key])
                            new_expiry = request.POST[expiry_key]
                            
                            # Update if changed
                            if (stock.quantity != new_quantity or 
                                float(stock.price) != new_price or 
                                str(stock.expiry_date) != new_expiry):
                                
                                stock.quantity = new_quantity
                                stock.price = new_price
                                stock.expiry_date = new_expiry
                                stock.save()
                                updated_count += 1
                                print(f"Updated stock {stock.id}")
                                
                        except (ValueError, KeyError) as e:
                            print(f"Error updating stock {stock.id}: {e}")
                            continue
            
            messages.success(request, f'Updated {updated_count} item(s)!' if updated_count > 0 else 'No changes made.')
            
        except Exception as e:
            print(f"Bulk update error: {e}")
            import traceback
            traceback.print_exc()
            messages.error(request, f'Error: {str(e)}')
        
        return redirect('pharmacy_home')
    
    return render(request, 'accounts/update_stock.html', {
        'stock_items': stocks,
        'stocks': stocks,
        'all_medicines': all_medicines,
        'pharmacy_name': pharmacy.pharmacy_id.name,
        'pharmacist_name': 'Ahmad Yateem',
    })


@login_required
def view_inventory(request):
    """View complete inventory with search and filters."""
    if request.user.role != User.Role.PHARMACY:
        return render(request, 'accounts/error.html', {
            'message': 'This page is for pharmacies only.'
        })
    
    try:
        pharmacy = request.user.pharmacy
    except Pharmacy.DoesNotExist:
        pharmacy = Pharmacy.objects.create(
            pharmacy_id=request.user,
            license_number=None,
            address=''
        )
    
    stocks = Stock.objects.filter(pharmacy=pharmacy).select_related('medicine')
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        stocks = stocks.filter(
            Q(medicine__name__icontains=search_query) |
            Q(medicine__dosage_form__icontains=search_query) |
            Q(medicine__strength__icontains=search_query)
        )
    
    # Filters
    today = timezone.localdate()
    expiry_threshold = today + timedelta(days=30)
    status_filter = request.GET.get('status', 'all')
    
    if status_filter == 'low':
        stocks = stocks.filter(quantity__lte=10)
    elif status_filter == 'expiring':
        stocks = stocks.filter(expiry_date__lte=expiry_threshold, expiry_date__gte=today)
    elif status_filter == 'expired':
        stocks = stocks.filter(expiry_date__lt=today)
    
    # Sort
    sort_by = request.GET.get('sort', 'name')
    if sort_by == 'name':
        stocks = stocks.order_by('medicine__name')
    elif sort_by == 'quantity':
        stocks = stocks.order_by('quantity')
    elif sort_by == 'expiry':
        stocks = stocks.order_by('expiry_date')
    
    # Build stock list with status
    stock_list = []
    for stock in stocks:
        status = 'ok'
        status_text = 'In Stock'
        
        if stock.expiry_date < today:
            status = 'expired'
            status_text = 'Expired'
        elif stock.expiry_date <= expiry_threshold:
            status = 'expiring'
            status_text = 'Expiring Soon'
        elif stock.quantity <= 10:
            status = 'low'
            status_text = 'Low Stock'
        
        stock_list.append({
            'id': stock.id,
            'medicine': stock.medicine,
            'quantity': stock.quantity,
            'price': stock.price,
            'expiry_date': stock.expiry_date,
            'status': status,
            'status_text': status_text,
        })
    
    return render(request, 'accounts/view_inventory.html', {
        'stock_items': stock_list,
        'stocks': stock_list,
        'search_query': search_query,
        'status_filter': status_filter,
        'sort_by': sort_by,
        'total_items': len(stock_list),
        'pharmacy_name': pharmacy.pharmacy_id.name,
        'pharmacist_name': 'Ahmad Yateem',
    })


@login_required
def delete_stock(request, stock_id):
    """Delete a stock entry."""
    if request.user.role != User.Role.PHARMACY:
        return render(request, 'accounts/error.html', {
            'message': 'This page is for pharmacies only.'
        })
    
    try:
        pharmacy = request.user.pharmacy
    except Pharmacy.DoesNotExist:
        pharmacy = Pharmacy.objects.create(
            pharmacy_id=request.user,
            license_number=None,
            address=''
        )
    
    try:
        stock = Stock.objects.get(id=stock_id, pharmacy=pharmacy)
        medicine_name = stock.medicine.name
        stock.delete()
        messages.success(request, f'Removed {medicine_name} from inventory.')
    except Stock.DoesNotExist:
        messages.error(request, 'Stock item not found.')
    
    return redirect('view_inventory')

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


# ============================================================================
# PATIENT PAGES
# ============================================================================
from datetime import datetime
from django.utils.dateparse import parse_date
from django.contrib import messages
from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Doctor, Appointment, Patient, User

@login_required
def schedule_appointment(request):
    """
    Page for patients to schedule new appointments with doctors.
    Supports optional pre-filled date/time when redirected from availability page.
    """
    user = request.user

    # Ensure user is a patient
    if user.role != User.Role.PATIENT:
        return render(request, "accounts/error.html", {
            "message": "This page is for patients only."
        })

    # Ensure patient profile exists
    try:
        patient_profile = user.patient
    except Patient.DoesNotExist:
        patient_profile = Patient.objects.create(
            patient_id=user,
            national_id='',
            dob=None,
            gender='',
            blood_type='',
            history_summary=''
        )

    # ✅ Handle form submission
    if request.method == "POST":
        doctor_id = request.POST.get("doctor")
        date_str = request.POST.get("date")
        time_str = request.POST.get("time")
        notes = request.POST.get("notes", "").strip()

        # --- Validation ---
        if not (doctor_id and date_str and time_str):
            messages.error(request, "Please select a doctor, date, and time.")
            return redirect("schedule_appointment")

        try:
            doctor = Doctor.objects.get(doctor_id__id=doctor_id)
        except Doctor.DoesNotExist:
            messages.error(request, "Selected doctor not found.")
            return redirect("schedule_appointment")

        try:
            the_date = parse_date(date_str)
            hour, minute = map(int, time_str.split(":"))
            tz = timezone.get_current_timezone()
            dt = timezone.make_aware(datetime(the_date.year, the_date.month, the_date.day, hour, minute), tz)
        except Exception:
            messages.error(request, "Invalid date or time format.")
            return redirect("schedule_appointment")

        # --- Check if slot is free ---
        if Appointment.objects.filter(doctor=doctor, date_time=dt, status=Appointment.Status.SCHEDULED).exists():
            messages.error(request, "This time slot is already booked.")
            return redirect("schedule_appointment")

        # --- Create the appointment ---
        Appointment.objects.create(
            doctor=doctor,
            patient=patient_profile,
            date_time=dt,
            notes=notes,  # ✅ save notes
            status=Appointment.Status.SCHEDULED,
        )

        messages.success(
            request,
            f"✅ Appointment booked successfully with {doctor.doctor_id.name} "
            f"on {the_date.strftime('%B %d, %Y')} at {dt.strftime('%I:%M %p')}."
        )
      
         # ✅ stay on same page and show message
        return redirect("schedule_appointment")


    # ✅ Original GET logic (kept intact)
    preset_date = request.GET.get("date")
    preset_time = request.GET.get("time")
    preset_doctor_id = request.GET.get("doctor")

    doctors = Doctor.objects.all().select_related('doctor_id')

    preset_doctor_name = None
    if preset_doctor_id:
        try:
            selected_doctor = Doctor.objects.get(doctor_id__id=preset_doctor_id)
            preset_doctor_name = selected_doctor.doctor_id.name
        except Doctor.DoesNotExist:
            preset_doctor_name = None

    context = {
        "patient_name": user.name or user.username,
        "today": timezone.localdate().strftime("%A, %B %d"),
        "doctors": doctors,
        "preset_date": preset_date,
        "preset_time": preset_time,
        "preset_doctor_id": preset_doctor_id,
        "preset_doctor_name": preset_doctor_name,
    }

    return render(request, "accounts/schedule_appointment.html", context)


    


@login_required
def view_medical_history(request):
    """
    Page for patients to view their medical history and test results
    """
    user = request.user

    # Check if user is a patient
    if user.role != User.Role.PATIENT:
        return render(request, "accounts/error.html", {
            "message": "This page is for patients only."
        })

    try:
        patient_profile = user.patient
    except Patient.DoesNotExist:
        patient_profile = Patient.objects.create(
            patient_id=user,
            national_id='',
            dob=None,
            gender='',
            blood_type='',
            history_summary=''
        )

    # Get patient's appointments history
    past_appointments = Appointment.objects.filter(
        patient=patient_profile,
        status=Appointment.Status.COMPLETED
    ).select_related('doctor__doctor_id').order_by('-date_time')[:10]

    # Get test results (if model exists)
    test_results = getattr(patient_profile, "test_results", []).all().order_by('-id') \
        if hasattr(patient_profile, "test_results") else []

    # Patient basic info
    patient_info = {
        'national_id': patient_profile.national_id or 'Not provided',
        'dob': patient_profile.dob.strftime('%B %d, %Y') if patient_profile.dob else 'Not provided',
        'gender': patient_profile.gender or 'Not provided',
        'blood_type': patient_profile.blood_type or 'Not provided',
        'history_summary': patient_profile.history_summary or 'No medical history recorded yet.',
    }

    context = {
        "patient_name": user.name or user.username,
        "today": timezone.localdate().strftime("%A, %B %d"),
        "patient_info": patient_info,
        "past_appointments": past_appointments,
        "test_results": test_results,
    }

    return render(request, "accounts/view_medical_history.html", context)


@login_required
def view_prescriptions(request):
    """
    Page for patients to view their prescriptions
    """
    user = request.user

    # Check if user is a patient
    if user.role != User.Role.PATIENT:
        return render(request, "accounts/error.html", {
            "message": "This page is for patients only."
        })

    try:
        patient_profile = user.patient
    except Patient.DoesNotExist:
        patient_profile = Patient.objects.create(
            patient_id=user,
            national_id='',
            dob=None,
            gender='',
            blood_type='',
            history_summary=''
        )

    # Ensure Prescribes model is imported
    try:
        from .models import Prescribes
    except ImportError:
        messages.error(request, "Prescribes model not found.")
        return render(request, "accounts/error.html", {"message": "Prescriptions feature not implemented yet."})

    # Get all prescriptions for this patient
    prescriptions = Prescribes.objects.filter(
        patient=patient_profile
    ).select_related('doctor__doctor_id', 'medicine').order_by('-date_prescribed')

    # Group prescriptions by date
    prescriptions_by_date = []
    for date, group in groupby(prescriptions, key=attrgetter('date_prescribed')):
        prescriptions_by_date.append({
            'date': date,
            'items': list(group)
        })

    context = {
        "patient_name": user.name or user.username,
        "today": timezone.localdate().strftime("%A, %B %d"),
        "prescriptions_by_date": prescriptions_by_date,
        "total_prescriptions": prescriptions.count(),
    }

    return render(request, "accounts/view_prescriptions.html", context)


@login_required
def browse_medicine(request):
    """
    Page for patients to browse available medicines
    """
    user = request.user

    # Check if user is a patient
    if user.role != User.Role.PATIENT:
        return render(request, "accounts/error.html", {
            "message": "This page is for patients only."
        })

    # Get search query
    search_query = request.GET.get('search', '').strip()

    # Only show medicines that actually have non-expired stock available
    today = timezone.localdate()

    base_stock_qs = Stock.objects.filter(
        quantity__gt=0,
        expiry_date__gte=today,
    )

    if search_query:
        base_stock_qs = base_stock_qs.filter(
            Q(medicine__name__icontains=search_query)
            | Q(medicine__dosage_form__icontains=search_query)
            | Q(medicine__strength__icontains=search_query)
            | Q(medicine__description__icontains=search_query)
        )

    # Get the set of medicine ids that are actually available
    available_medicine_ids = list(
        base_stock_qs.values_list('medicine_id', flat=True).distinct()
    )

    # Prefetch only available stocks for these medicines, cheapest first
    prefetch_available = Prefetch(
        'stocks',
        queryset=Stock.objects.filter(
            quantity__gt=0,
            expiry_date__gte=today,
        )
        .select_related('pharmacy__pharmacy_id')
        .order_by('price'),
        to_attr='available_stocks',
    )

    medicines = (
        Medicine.objects.filter(id__in=available_medicine_ids)
        .order_by('name')
        .prefetch_related(prefetch_available)
    )

    # Build medicine list with per-pharmacy availability (top 3 by best price)
    medicine_list = []
    for m in medicines:
        # Group by pharmacy, keep best price and sum quantity
        by_pharmacy = {}
        for s in getattr(m, 'available_stocks', []):
            pid = s.pharmacy_id
            pname = s.pharmacy.pharmacy_id.name
            entry = by_pharmacy.get(pid)
            if not entry:
                by_pharmacy[pid] = {
                    'pharmacy_name': pname,
                    'price': s.price,
                    'quantity': s.quantity,
                }
            else:
                # Keep lowest price, sum quantities
                if s.price < entry['price']:
                    entry['price'] = s.price
                entry['quantity'] += s.quantity

        pharmacies = sorted(by_pharmacy.values(), key=lambda x: x['price'])

        medicine_list.append({
            'medicine': m,
            'in_stock': len(pharmacies) > 0,
            'pharmacies': pharmacies[:3],
            'total_pharmacies': len(pharmacies),
        })

    context = {
        'patient_name': user.name or user.username,
        'today': today.strftime('%A, %B %d'),
        'medicine_list': medicine_list,
        'search_query': search_query,
        'total_medicines': len(medicine_list),
    }

    return render(request, 'accounts/browse_medicine.html', context)

@login_required
def view_doctor_availability(request, doctor_id):
    """Allow patients to view a doctor's weekly schedule and booked slots."""
    # Ensure only patients can access
    if request.user.role != User.Role.PATIENT:
        return render(request, "accounts/error.html", {
            "message": "This page is for patients only."
        })

    # Get doctor profile
    try:
        doctor = Doctor.objects.get(pk=doctor_id)
    except Doctor.DoesNotExist:
        messages.error(request, "Doctor not found.")
        return redirect("schedule_appointment")

    today = timezone.localdate()
    date_str = request.GET.get("date")
    selected_date = parse_date(date_str) if date_str else today

    week_start = selected_date - timedelta(days=selected_date.weekday())
    week_end = week_start + timedelta(days=6)
    tz = timezone.get_current_timezone()

    # Get weekly working hours
    working_hours = DoctorWorkingHours.objects.filter(doctor=doctor).order_by("day_of_week")

    # Get all appointments + timeoffs in this week
    appointments = Appointment.objects.filter(
        doctor=doctor,
        date_time__date__gte=week_start,
        date_time__date__lte=week_end,
        status=Appointment.Status.SCHEDULED
    )
    timeoffs = DoctorTimeOff.objects.filter(
        doctor=doctor,
        date__gte=week_start,
        date__lte=week_end
    )

    # Build availability grid
    week_data = []
    for day_offset in range(7):
        current_date = week_start + timedelta(days=day_offset)
        dow = current_date.weekday() + 1
        hours = working_hours.filter(day_of_week=dow).first()

        if not hours:
            week_data.append({
                "date": current_date,
                "weekday": current_date.strftime("%A"),
                "slots": [],
                "available": False,
                "note": "No working hours"
            })
            continue

        # Compute all slots for that day (15-minute steps)
        start_dt = timezone.make_aware(datetime.combine(current_date, hours.start_time), tz)
        end_dt = timezone.make_aware(datetime.combine(current_date, hours.end_time), tz)
        slot_time = start_dt
        slots = []

        while slot_time < end_dt:
            slot_str = slot_time.strftime("%H:%M")

            # mark as busy if appointment overlaps within 15min
            slot_busy = appointments.filter(
                date_time__gte=slot_time,
                date_time__lt=slot_time + timedelta(minutes=15)
            ).exists()

            # Check time off overlap
            off_blocked = any(
                off.date == current_date and
                off.start_time <= slot_time.time() < off.end_time
                for off in timeoffs
            )

            if slot_busy:
                status = "booked"
            elif off_blocked:
                status = "timeoff"
            else:
                status = "free"

            slots.append({"time": slot_str, "status": status})
            slot_time += timedelta(minutes=15)

        week_data.append({
            "date": current_date,
            "weekday": current_date.strftime("%A"),
            "slots": slots,
            "available": True
        })

    context = {
        "doctor": doctor,
        "week_start": week_start,
        "week_end": week_end,
        "week_data": week_data,
        "today": today,
    }
    return render(request, "accounts/view_doctor_availability.html", context)


@login_required
def view_medical_history(request):
    """Display and allow editing of a patient's medical info, past appointments, and test results."""
    if request.user.role != User.Role.PATIENT:
        return render(request, "accounts/error.html", {"message": "This page is for patients only."})

    patient = request.user.patient  # assuming 1-to-1 relation
    past_appointments = Appointment.objects.filter(
        patient=patient,
        status=Appointment.Status.COMPLETED
    ).order_by("-date_time")

    test_results = TestResult.objects.filter(patient=patient) if hasattr(patient, "testresult_set") else []

    # ✅ Handle edits
    if request.method == "POST":
        national_id = request.POST.get("national_id", "").strip()
        dob = request.POST.get("dob") or None
        gender = request.POST.get("gender", "").strip()
        blood_type = request.POST.get("blood_type", "").strip()
        summary = request.POST.get("history_summary", "").strip()

        patient.national_id = national_id
        patient.dob = dob
        patient.gender = gender
        patient.blood_type = blood_type
        patient.history_summary = summary
        patient.save()

        messages.success(request, "✅ Medical information updated successfully.")
        return redirect("view_medical_history")

    context = {
        "patient_name": request.user.name or request.user.username,
        "today": timezone.localdate().strftime("%A, %B %d"),
        "patient_info": patient,
        "past_appointments": past_appointments,
        "test_results": test_results,
        "blood_types": ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"],  # ✅ add this
    }
    return render(request, "accounts/view_medical_history.html", context)

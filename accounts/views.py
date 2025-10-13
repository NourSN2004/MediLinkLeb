from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from django.utils import timezone
from .models import Appointment, Patient, Doctor, User, Pharmacy, Stock, Medicine
from .services import AuthenticationService
from django.db.models import Q, Count, Sum
from datetime import timedelta
from django.db import transaction, IntegrityError
from .forms import SignUpForm, ForgotPasswordForm, ResetPasswordForm, MedicineForm, StockForm, NewMedicineStockForm, StockUpdateForm
import logging

logger = logging.getLogger(__name__)

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
            license_number=None
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
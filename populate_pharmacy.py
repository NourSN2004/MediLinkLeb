"""
Populate the database with sample medicines and stock for pharmacy testing.
"""
import os
import django
from datetime import datetime, timedelta
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from accounts.models import User, Pharmacy, Medicine, Stock

def populate():
    # Get or create a pharmacy user
    try:
        pharmacy_user = User.objects.get(username='ahmadyateemm@gmail.com')
        print(f"Found pharmacy user: {pharmacy_user.username}")
    except User.DoesNotExist:
        print("Pharmacy user 'ahmadyateemm@gmail.com' not found. Please create one first.")
        return
    
    # Get or create the pharmacy profile
    try:
        pharmacy = pharmacy_user.pharmacy
        print(f"Found pharmacy profile for: {pharmacy_user.name}")
    except Pharmacy.DoesNotExist:
        print("Creating pharmacy profile...")
        pharmacy = Pharmacy.objects.create(
            pharmacy_id=pharmacy_user,
            license_number=None,
            address='123 Medical Street, Beirut'
        )
        print(f"Created pharmacy profile")
    
    # Sample medicines data
    medicines_data = [
        # Name, Dosage Form, Strength, Description
        ('Paracetamol', 'Tablet', '500mg', 'Pain reliever and fever reducer'),
        ('Ibuprofen', 'Tablet', '400mg', 'Anti-inflammatory and pain relief'),
        ('Amoxicillin', 'Capsule', '500mg', 'Antibiotic for bacterial infections'),
        ('Aspirin', 'Tablet', '100mg', 'Pain relief and blood thinner'),
        ('Omeprazole', 'Capsule', '20mg', 'Reduces stomach acid'),
        ('Metformin', 'Tablet', '850mg', 'Diabetes medication'),
        ('Lisinopril', 'Tablet', '10mg', 'Blood pressure medication'),
        ('Atorvastatin', 'Tablet', '20mg', 'Cholesterol-lowering medication'),
        ('Cetirizine', 'Tablet', '10mg', 'Antihistamine for allergies'),
        ('Salbutamol', 'Inhaler', '100mcg', 'Asthma relief inhaler'),
        ('Cough Syrup', 'Syrup', '100ml', 'Relief for cough and cold'),
        ('Vitamin D', 'Capsule', '1000IU', 'Vitamin D supplement'),
        ('Multivitamin', 'Tablet', 'Daily', 'Complete daily vitamin supplement'),
        ('Insulin Glargine', 'Injection', '100IU/ml', 'Long-acting insulin'),
        ('Diazepam', 'Tablet', '5mg', 'Anxiety and muscle relaxant'),
    ]
    
    print("\nCreating medicines...")
    medicines = []
    for name, form, strength, desc in medicines_data:
        medicine, created = Medicine.objects.get_or_create(
            name=name,
            dosage_form=form,
            strength=strength,
            defaults={'description': desc}
        )
        medicines.append(medicine)
        if created:
            print(f"  ✓ Created: {medicine}")
        else:
            print(f"  - Already exists: {medicine}")
    
    # Create stock entries with varying expiry dates and quantities
    print("\nCreating stock entries...")
    today = datetime.now().date()
    
    stock_data = [
        # Medicine index, days until expiry, quantity, price
        (0, 30, 8, 2.50),      # Paracetamol - expiring soon, low stock
        (1, 45, 12, 3.75),     # Ibuprofen - expiring soon
        (2, 60, 5, 8.50),      # Amoxicillin - very low stock
        (3, 90, 25, 1.25),     # Aspirin - good stock
        (4, 120, 18, 12.00),   # Omeprazole
        (5, 150, 30, 5.50),    # Metformin - good stock
        (6, 180, 22, 7.25),    # Lisinopril
        (7, 200, 15, 15.00),   # Atorvastatin
        (8, 240, 9, 4.50),     # Cetirizine - low stock
        (9, 280, 7, 18.00),    # Salbutamol - low stock
        (10, 300, 20, 6.75),   # Cough Syrup
        (11, 330, 35, 3.25),   # Vitamin D - good stock
        (12, 360, 28, 8.99),   # Multivitamin
        (13, 20, 3, 45.00),    # Insulin - CRITICAL: expiring very soon & very low
        (14, 400, 40, 2.15),   # Diazepam - good stock
    ]
    
    for med_idx, days_until_expiry, quantity, price in stock_data:
        medicine = medicines[med_idx]
        expiry_date = today + timedelta(days=days_until_expiry)
        
        stock, created = Stock.objects.get_or_create(
            pharmacy=pharmacy,
            medicine=medicine,
            expiry_date=expiry_date,
            defaults={
                'quantity': quantity,
                'price': Decimal(str(price))
            }
        )
        
        if created:
            status = "CRITICAL" if quantity <= 5 else "LOW" if quantity <= 10 else "OK"
            expiry_status = "URGENT" if days_until_expiry <= 30 else "SOON" if days_until_expiry <= 60 else "OK"
            print(f"  ✓ {medicine.name}: {quantity} units, expires in {days_until_expiry} days [{status}/{expiry_status}]")
        else:
            # Update existing stock
            stock.quantity = quantity
            stock.price = Decimal(str(price))
            stock.save()
            print(f"  - Updated: {medicine.name}")
    
    print("\n" + "="*60)
    print("DATABASE POPULATED SUCCESSFULLY!")
    print("="*60)
    print(f"\nTotal Medicines: {len(medicines)}")
    print(f"Total Stock Items: {len(stock_data)}")
    print(f"Pharmacy: {pharmacy_user.name}")
    
    # Summary statistics
    total_stock = Stock.objects.filter(pharmacy=pharmacy)
    low_stock = total_stock.filter(quantity__lte=10).count()
    expiring_soon = total_stock.filter(expiry_date__lte=today + timedelta(days=60)).count()
    critical = total_stock.filter(quantity__lte=5).count()
    
    print(f"\nStock Summary:")
    print(f"  - Low Stock (≤10 units): {low_stock}")
    print(f"  - Critical Stock (≤5 units): {critical}")
    print(f"  - Expiring Soon (≤60 days): {expiring_soon}")
    print("\nYou can now log in and test the pharmacy dashboard!")

if __name__ == '__main__':
    populate()

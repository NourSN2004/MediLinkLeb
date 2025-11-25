
import os
import sys
import django
from datetime import date, timedelta
import random
from decimal import Decimal

sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventory_service.settings')
django.setup()

from inventory.models import Medicine, PharmacyStock

pharmacy_id = 3

print(f"Populating CRITICAL stock for Pharmacy ID {pharmacy_id}...")

medicines = Medicine.objects.all()
if not medicines.exists():
    print("No medicines found! Run populate_inventory.py first.")
    sys.exit(1)

# 1. Add Low Stock Items (Quantity <= Reorder Level)
low_stock_meds = medicines[5:8] # Use next 3 medicines
for med in low_stock_meds:
    stock, created = PharmacyStock.objects.get_or_create(
        pharmacy_id=pharmacy_id,
        medicine=med,
        defaults={
            'quantity': 5, # Low stock
            'selling_price': med.base_price * Decimal('1.2'),
            'expiry_date': date.today() + timedelta(days=365),
            'reorder_level': 10,
            'batch_number': f'LOW-{random.randint(1000, 9999)}'
        }
    )
    if created:
        print(f"Added LOW STOCK item: {med.name}")
    else:
        # Force update to low stock if exists
        stock.quantity = 5
        stock.reorder_level = 10
        stock.save()
        print(f"Updated to LOW STOCK: {med.name}")

# 2. Add Expiring Soon Items (Expiry <= Today + 30 days)
expiring_meds = medicines[8:11] # Use next 3 medicines
for med in expiring_meds:
    stock, created = PharmacyStock.objects.get_or_create(
        pharmacy_id=pharmacy_id,
        medicine=med,
        defaults={
            'quantity': 100,
            'selling_price': med.base_price * Decimal('1.2'),
            'expiry_date': date.today() + timedelta(days=15), # Expiring soon
            'reorder_level': 10,
            'batch_number': f'EXP-{random.randint(1000, 9999)}'
        }
    )
    if created:
        print(f"Added EXPIRING SOON item: {med.name}")
    else:
        # Force update to expiring soon
        stock.expiry_date = date.today() + timedelta(days=15)
        stock.save()
        print(f"Updated to EXPIRING SOON: {med.name}")

# 3. Add Expired Items (Expiry < Today)
expired_meds = medicines[11:13] # Use next 2 medicines
for med in expired_meds:
    stock, created = PharmacyStock.objects.get_or_create(
        pharmacy_id=pharmacy_id,
        medicine=med,
        defaults={
            'quantity': 50,
            'selling_price': med.base_price * Decimal('1.2'),
            'expiry_date': date.today() - timedelta(days=5), # Expired
            'reorder_level': 10,
            'batch_number': f'OLD-{random.randint(1000, 9999)}'
        }
    )
    if created:
        print(f"Added EXPIRED item: {med.name}")
    else:
        stock.expiry_date = date.today() - timedelta(days=5)
        stock.save()
        print(f"Updated to EXPIRED: {med.name}")

print("Done. Critical stock items populated.")

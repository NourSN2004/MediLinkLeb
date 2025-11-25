"""
Populate Inventory Service with sample medicines
"""
import os
import django
import sys
import random
from datetime import date, timedelta
from decimal import Decimal

# Setup Django environment
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventory_service.settings')
django.setup()

from inventory.models import Medicine, PharmacyStock

# Sample medicines
medicines = [
    {
        'name': 'Paracetamol',
        'generic_name': 'Acetaminophen',
        'manufacturer': 'PharmaCorp',
        'form': 'Tablet',
        'strength': '500mg',
        'category': 'Analgesic',
        'requires_prescription': False,
        'base_price': 2.50,
        'description': 'Pain reliever and fever reducer'
    },
    {
        'name': 'Amoxicillin',
        'generic_name': 'Amoxicillin',
        'manufacturer': 'MedLab',
        'form': 'Capsule',
        'strength': '500mg',
        'category': 'Antibiotic',
        'requires_prescription': True,
        'base_price': 15.00,
        'description': 'Penicillin antibiotic'
    },
    {
        'name': 'Ibuprofen',
        'generic_name': 'Ibuprofen',
        'manufacturer': 'HealthPlus',
        'form': 'Tablet',
        'strength': '400mg',
        'category': 'NSAID',
        'requires_prescription': False,
        'base_price': 5.00,
        'description': 'Anti-inflammatory pain reliever'
    },
    {
        'name': 'Omeprazole',
        'generic_name': 'Omeprazole',
        'manufacturer': 'GastroCare',
        'form': 'Capsule',
        'strength': '20mg',
        'category': 'Proton Pump Inhibitor',
        'requires_prescription': True,
        'base_price': 12.00,
        'description': 'Treats stomach acid problems'
    },
    {
        'name': 'Metformin',
        'generic_name': 'Metformin Hydrochloride',
        'manufacturer': 'DiabetesRx',
        'form': 'Tablet',
        'strength': '500mg',
        'category': 'Antidiabetic',
        'requires_prescription': True,
        'base_price': 8.00,
        'description': 'Type 2 diabetes medication'
    },
    {
        'name': 'Cetirizine',
        'generic_name': 'Cetirizine',
        'manufacturer': 'AllergyCare',
        'form': 'Tablet',
        'strength': '10mg',
        'category': 'Antihistamine',
        'requires_prescription': False,
        'base_price': 6.00,
        'description': 'Allergy relief medication'
    },
    {
        'name': 'Losartan',
        'generic_name': 'Losartan Potassium',
        'manufacturer': 'CardioMed',
        'form': 'Tablet',
        'strength': '50mg',
        'category': 'Antihypertensive',
        'requires_prescription': True,
        'base_price': 10.00,
        'description': 'Blood pressure medication'
    },
    {
        'name': 'Vitamin D3',
        'generic_name': 'Cholecalciferol',
        'manufacturer': 'VitaHealth',
        'form': 'Capsule',
        'strength': '1000 IU',
        'category': 'Vitamin Supplement',
        'requires_prescription': False,
        'base_price': 7.50,
        'description': 'Vitamin D supplement'
    },
    {
        'name': 'Aspirin',
        'generic_name': 'Acetylsalicylic Acid',
        'manufacturer': 'CardioPlus',
        'form': 'Tablet',
        'strength': '81mg',
        'category': 'Antiplatelet',
        'requires_prescription': False,
        'base_price': 3.00,
        'description': 'Low-dose aspirin for heart health'
    },
    {
        'name': 'Atorvastatin',
        'generic_name': 'Atorvastatin Calcium',
        'manufacturer': 'CardioMed',
        'form': 'Tablet',
        'strength': '20mg',
        'category': 'Statin',
        'requires_prescription': True,
        'base_price': 18.00,
        'description': 'Cholesterol-lowering medication'
    },
]

print("Creating medicines...")
created_count = 0
for med_data in medicines:
    medicine, created = Medicine.objects.get_or_create(
        name=med_data['name'],
        strength=med_data['strength'],
        defaults=med_data
    )
    if created:
        created_count += 1
        print(f"✓ Created: {medicine.name} {medicine.strength}")
    else:
        print(f"- Already exists: {medicine.name} {medicine.strength}")

print(f"\n✅ Complete! {created_count} new medicines added.")
print(f"📊 Total medicines in catalog: {Medicine.objects.count()}")

# ============================================================================
# POPULATE STOCK FOR PHARMACY
# ============================================================================

pharmacy_id = 3  # pharmacy1@medilink.com user ID

print(f"\n{'='*60}")
print(f"Populating stock for Pharmacy ID {pharmacy_id}...")
print(f"{'='*60}\n")

all_medicines = Medicine.objects.all()
if not all_medicines.exists():
    print("No medicines found!")
    sys.exit(1)

# Stock configuration: (medicine_index, quantity, days_until_expiry, reorder_level)
# Designed to include LOW STOCK, EXPIRING SOON, and EXPIRED items
stock_config = [
    # CRITICAL ITEMS - Low Stock
    (5, 5, 365, 10),   # Cetirizine - LOW STOCK
    (6, 8, 180, 10),   # Losartan - LOW STOCK
    (7, 3, 200, 10),   # Vitamin D3 - CRITICAL LOW STOCK
    
    # CRITICAL ITEMS - Expiring Soon (within 30 days)
    (8, 100, 15, 10),  # Aspirin - EXPIRING SOON
    (9, 80, 20, 10),   # Atorvastatin - EXPIRING SOON
    (0, 120, 25, 10),  # Paracetamol - EXPIRING SOON
    
    # CRITICAL ITEMS - Expired
    (1, 50, -5, 10),   # Amoxicillin - EXPIRED
    (2, 30, -10, 10),  # Ibuprofen - EXPIRED
    
    # NORMAL STOCK
    (3, 150, 180, 20), # Omeprazole - Good stock
    (4, 200, 240, 20), # Metformin - Good stock
]

stock_count = 0
for med_idx, quantity, days_offset, reorder in stock_config:
    if med_idx >= len(all_medicines):
        continue
    
    med = all_medicines[med_idx]
    expiry = date.today() + timedelta(days=days_offset)
    
    stock, created = PharmacyStock.objects.get_or_create(
        pharmacy_id=pharmacy_id,
        medicine=med,
        defaults={
            'quantity': quantity,
            'selling_price': med.base_price * Decimal('1.2'),
            'expiry_date': expiry,
            'reorder_level': reorder,
            'batch_number': f'BATCH-{random.randint(1000, 9999)}'
        }
    )
    
    if created:
        status = "CRITICAL" if quantity <= 5 else "LOW" if quantity <= 10 else "OK"
        exp_status = "EXPIRED" if days_offset < 0 else "EXPIRING SOON" if days_offset <= 30 else "OK"
        print(f"Added stock: {med.name:20} | Qty: {quantity:3} [{status:8}] | Expiry: {days_offset:4} days [{exp_status:13}]")
        stock_count += 1
    else:
        # Update existing stock to match config
        stock.quantity = quantity
        stock.expiry_date = expiry
        stock.reorder_level = reorder
        stock.save()
        print(f"Updated: {med.name}")

print(f"\n✅ Stock population complete! Added/Updated {stock_count} stock items.")
print(f"📊 Total stock items for pharmacy {pharmacy_id}: {PharmacyStock.objects.filter(pharmacy_id=pharmacy_id).count()}")

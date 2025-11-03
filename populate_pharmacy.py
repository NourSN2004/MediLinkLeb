"""
Populate the database with sample medicines and stock for pharmacy testing.
"""
import os
from datetime import datetime, timedelta
from decimal import Decimal

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
django.setup()

from accounts.models import User, Pharmacy, Medicine, Stock  # noqa: E402  pylint: disable=wrong-import-position


def ensure_pharmacies():
    """
    Ensure every pharmacy user has an associated Pharmacy profile.
    Returns a list of Pharmacy instances that will be populated.
    """
    pharmacy_users = User.objects.filter(role=User.Role.PHARMACY)

    if not pharmacy_users.exists():
        print("No pharmacy user accounts found. Please create at least one pharmacy account.")
        return []

    pharmacies = []
    for user in pharmacy_users:
        pharmacy, created = Pharmacy.objects.get_or_create(
            pharmacy_id=user,
            defaults={
                "license_number": None,
                "address": "123 Medical Street, Beirut",
            },
        )
        action = "Created" if created else "Found"
        print(f"{action} pharmacy profile for: {user.email}")
        pharmacies.append(pharmacy)
    return pharmacies


def create_medicines():
    """
    Create the shared catalogue of medicines used by every pharmacy.
    Returns a list of Medicine instances aligned with the stock_data order.
    """
    medicines_data = [
        # Name, Dosage Form, Strength, Description
        ("Paracetamol", "Tablet", "500mg", "Pain reliever and fever reducer"),
        ("Ibuprofen", "Tablet", "400mg", "Anti-inflammatory and pain relief"),
        ("Amoxicillin", "Capsule", "500mg", "Antibiotic for bacterial infections"),
        ("Aspirin", "Tablet", "100mg", "Pain relief and blood thinner"),
        ("Omeprazole", "Capsule", "20mg", "Reduces stomach acid"),
        ("Metformin", "Tablet", "850mg", "Diabetes medication"),
        ("Lisinopril", "Tablet", "10mg", "Blood pressure medication"),
        ("Atorvastatin", "Tablet", "20mg", "Cholesterol-lowering medication"),
        ("Cetirizine", "Tablet", "10mg", "Antihistamine for allergies"),
        ("Salbutamol", "Inhaler", "100mcg", "Asthma relief inhaler"),
        ("Cough Syrup", "Syrup", "100ml", "Relief for cough and cold"),
        ("Vitamin D", "Capsule", "1000IU", "Vitamin D supplement"),
        ("Multivitamin", "Tablet", "Daily", "Complete daily vitamin supplement"),
        ("Insulin Glargine", "Injection", "100IU/ml", "Long-acting insulin"),
        ("Diazepam", "Tablet", "5mg", "Anxiety and muscle relaxant"),
    ]

    print("\nCreating medicines...")
    medicines = []
    for name, form, strength, desc in medicines_data:
        medicine, created = Medicine.objects.get_or_create(
            name=name,
            dosage_form=form,
            strength=strength,
            defaults={"description": desc},
        )
        medicines.append(medicine)
        if created:
            print(f"  - Created: {medicine}")
        else:
            print(f"  - Already exists: {medicine}")
    return medicines


def populate_stock(pharmacies, medicines):
    """
    Populate stock entries for every pharmacy using the shared medicines list.
    """
    print("\nCreating stock entries...")
    today = datetime.now().date()
    stock_data = [
        # Medicine index, days until expiry, quantity, price
        (0, 30, 8, 2.50),  # Paracetamol - expiring soon, low stock
        (1, 45, 12, 3.75),  # Ibuprofen - expiring soon
        (2, 60, 5, 8.50),  # Amoxicillin - very low stock
        (3, 90, 25, 1.25),  # Aspirin - good stock
        (4, 120, 18, 12.00),  # Omeprazole
        (5, 150, 30, 5.50),  # Metformin - good stock
        (6, 180, 22, 7.25),  # Lisinopril
        (7, 200, 15, 15.00),  # Atorvastatin
        (8, 240, 9, 4.50),  # Cetirizine - low stock
        (9, 280, 7, 18.00),  # Salbutamol - low stock
        (10, 300, 20, 6.75),  # Cough Syrup
        (11, 330, 35, 3.25),  # Vitamin D - good stock
        (12, 360, 28, 8.99),  # Multivitamin
        (13, 20, 3, 45.00),  # Insulin - critical: expiring very soon & very low
        (14, 400, 40, 2.15),  # Diazepam - good stock
    ]

    for pharmacy in pharmacies:
        print(
            f"\nPopulating stock for {pharmacy.pharmacy_id.name} "
            f"({pharmacy.pharmacy_id.email})..."
        )
        for med_idx, days_until_expiry, quantity, price in stock_data:
            medicine = medicines[med_idx]
            expiry_date = today + timedelta(days=days_until_expiry)
            stock, created = Stock.objects.update_or_create(
                pharmacy=pharmacy,
                medicine=medicine,
                expiry_date=expiry_date,
                defaults={
                    "quantity": quantity,
                    "price": Decimal(str(price)),
                },
            )
            if created:
                status = "CRITICAL" if quantity <= 5 else "LOW" if quantity <= 10 else "OK"
                expiry_status = (
                    "URGENT" if days_until_expiry <= 30 else "SOON" if days_until_expiry <= 60 else "OK"
                )
                print(
                    f"  - Created {medicine.name}: {quantity} units, "
                    f"expires in {days_until_expiry} days [{status}/{expiry_status}]"
                )
            else:
                print(f"  - Updated: {medicine.name}")

        summarize_stock(pharmacy, today)


def summarize_stock(pharmacy, today):
    """
    Print stock summary information for a single pharmacy.
    """
    total_stock = Stock.objects.filter(pharmacy=pharmacy)
    low_stock = total_stock.filter(quantity__lte=10).count()
    expiring_soon = total_stock.filter(expiry_date__lte=today + timedelta(days=60)).count()
    critical = total_stock.filter(quantity__lte=5).count()

    print("Stock summary:")
    print(f"  - Low Stock (<=10 units): {low_stock}")
    print(f"  - Critical Stock (<=5 units): {critical}")
    print(f"  - Expiring Soon (<=60 days): {expiring_soon}")


def populate():
    pharmacies = ensure_pharmacies()
    if not pharmacies:
        return

    medicines = create_medicines()
    populate_stock(pharmacies, medicines)

    print("\n" + "=" * 60)
    print("DATABASE POPULATED SUCCESSFULLY!")
    print("=" * 60)
    print(f"\nTotal Medicines: {len(medicines)}")
    total_stock_items = Stock.objects.filter(pharmacy__in=pharmacies).count()
    print(f"Total Stock Items: {total_stock_items}")
    print(f"Pharmacies Populated: {len(pharmacies)}")


if __name__ == "__main__":
    populate()

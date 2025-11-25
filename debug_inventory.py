"""
Debug script to check medicines and stock in the database
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from accounts.models import User, Pharmacy, Medicine, Stock

def debug_inventory():
    print("="*60)
    print("PHARMACY INVENTORY DEBUG")
    print("="*60)
    
    # Get pharmacy user
    try:
        pharmacy_user = User.objects.get(username='ahmadyateemm@gmail.com')
        print(f"\nFound pharmacy user: {pharmacy_user.username}")
    except User.DoesNotExist:
        print("\nPharmacy user not found!")
        return
    
    # Get pharmacy profile
    try:
        pharmacy = pharmacy_user.pharmacy
        print(f"Found pharmacy profile: {pharmacy_user.name}")
    except Exception as e:
        print(f"Error getting pharmacy profile: {e}")
        return
    
    # Check all medicines in database
    all_medicines = Medicine.objects.all()
    print(f"\nTotal medicines in database: {all_medicines.count()}")
    
    # Check stock for this pharmacy
    pharmacy_stock = Stock.objects.filter(pharmacy=pharmacy)
    print(f"Stock items for this pharmacy: {pharmacy_stock.count()}")
    
    print("\n" + "="*60)
    print("MEDICINES IN DATABASE:")
    print("="*60)
    for med in all_medicines:
        print(f"  {med.id}. {med.name} - {med.strength} ({med.dosage_form})")
    
    print("\n" + "="*60)
    print("STOCK FOR THIS PHARMACY:")
    print("="*60)
    if pharmacy_stock.exists():
        for stock in pharmacy_stock.select_related('medicine'):
            print(f"  {stock.medicine.name} - {stock.quantity} units @ ${stock.price}")
            print(f"    Expires: {stock.expiry_date}")
    else:
        print("  No stock found for this pharmacy!")
    
    print("\n" + "="*60)
    print("MEDICINES WITHOUT STOCK:")
    print("="*60)
    medicines_with_stock = pharmacy_stock.values_list('medicine_id', flat=True)
    medicines_without_stock = all_medicines.exclude(id__in=medicines_with_stock)
    
    if medicines_without_stock.exists():
        for med in medicines_without_stock:
            print(f"  WARNING: {med.name} - {med.strength} ({med.dosage_form})")
        print(f"\n  Total: {medicines_without_stock.count()} medicines need stock entries")
    else:
        print("  All medicines have stock entries!")
    
    print("\n" + "="*60)

if __name__ == '__main__':
    debug_inventory()

"""
Populate medicine database with common medications
Run this inside inventory-service pod
"""
medicines_data = [
    # Name, Generic Name, Category, Description, Unit
    ("Paracetamol 500mg", "Paracetamol", "Pain Relief", "Pain reliever and fever reducer", "Tablet"),
    ("Ibuprofen 400mg", "Ibuprofen", "Pain Relief", "Anti-inflammatory and pain relief", "Tablet"),
    ("Amoxicillin 500mg", "Amoxicillin", "Antibiotic", "Antibiotic for bacterial infections", "Capsule"),
    ("Aspirin 100mg", "Acetylsalicylic Acid", "Cardiovascular", "Pain relief and blood thinner", "Tablet"),
    ("Omeprazole 20mg", "Omeprazole", "Gastro", "Reduces stomach acid", "Capsule"),
    ("Metformin 850mg", "Metformin", "Diabetes", "Diabetes medication", "Tablet"),
    ("Lisinopril 10mg", "Lisinopril", "Cardiovascular", "Blood pressure medication", "Tablet"),
    ("Atorvastatin 20mg", "Atorvastatin", "Cardiovascular", "Cholesterol-lowering medication", "Tablet"),
    ("Cetirizine 10mg", "Cetirizine", "Allergy", "Antihistamine for allergies", "Tablet"),
    ("Salbutamol Inhaler", "Salbutamol", "Respiratory", "Asthma relief inhaler", "Inhaler"),
    ("Cough Syrup", "Dextromethorphan", "Respiratory", "Relief for cough and cold", "Syrup"),
    ("Vitamin D 1000IU", "Cholecalciferol", "Supplement", "Vitamin D supplement", "Capsule"),
    ("Multivitamin", "Mixed Vitamins", "Supplement", "Complete daily vitamin supplement", "Tablet"),
    ("Insulin Glargine", "Insulin Glargine", "Diabetes", "Long-acting insulin", "Injection"),
    ("Diazepam 5mg", "Diazepam", "Psychiatric", "Anxiety and muscle relaxant", "Tablet"),
    ("Ciprofloxacin 500mg", "Ciprofloxacin", "Antibiotic", "Broad-spectrum antibiotic", "Tablet"),
    ("Losartan 50mg", "Losartan", "Cardiovascular", "Blood pressure medication", "Tablet"),
    ("Gabapentin 300mg", "Gabapentin", "Neurological", "Nerve pain medication", "Capsule"),
    ("Pantoprazole 40mg", "Pantoprazole", "Gastro", "Proton pump inhibitor", "Tablet"),
    ("Amlodipine 5mg", "Amlodipine", "Cardiovascular", "Calcium channel blocker", "Tablet"),
]

from inventory.models import Medicine

print("Creating medicines...")
created = 0
for name, generic, category, desc, unit in medicines_data:
    med, created_flag = Medicine.objects.get_or_create(
        name=name,
        defaults={
            'generic_name': generic,
            'category': category,
            'description': desc,
            'unit': unit,
            'is_active': True
        }
    )
    if created_flag:
        created += 1
        print(f"  ✓ Created: {name}")
    else:
        print(f"  - Exists: {name}")

print(f"\n✓ Total medicines: {Medicine.objects.count()}")
print(f"✓ Newly created: {created}")

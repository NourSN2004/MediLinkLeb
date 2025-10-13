from django import forms
from django.contrib.auth import get_user_model
from .models import Medicine, Stock
from django.core.exceptions import ValidationError

User = get_user_model()

USER_TYPE_CHOICES = [
    ('patient', 'Patient'),
    ('doctor', 'Doctor'),
    ('pharmacy', 'Pharmacy'),
]


class UserTypeForm(forms.Form):
    user_type = forms.ChoiceField(
        choices=USER_TYPE_CHOICES,
        widget=forms.RadioSelect,
        label='Choose your account type'
    )


class SignUpForm(forms.Form):
    email = forms.EmailField(required=True, label='Email')
    first_name = forms.CharField(max_length=150, required=False, label='First Name')
    last_name = forms.CharField(max_length=150, required=False, label='Last Name')
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2


class LoginForm(forms.Form):
    email = forms.EmailField(label='Email')
    password = forms.CharField(label='Password', widget=forms.PasswordInput)


class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(label='Email')


class ResetPasswordForm(forms.Form):
    password1 = forms.CharField(label='New Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

class MedicineForm(forms.ModelForm):
    """Form for adding a new medicine to the catalog."""
    
    class Meta:
        model = Medicine
        fields = ['name', 'strength', 'dosage_form', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Paracetamol',
                'required': True
            }),
            'strength': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 500mg',
                'required': True
            }),
            'dosage_form': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Tablet, Capsule, Syrup',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional: Additional information about the medicine'
            }),
        }
        labels = {
            'name': 'Medicine Name',
            'strength': 'Strength',
            'dosage_form': 'Dosage Form',
            'description': 'Description',
        }
    
class StockForm(forms.ModelForm):
    """Form for adding stock to an existing medicine."""
    
    class Meta:
        model = Stock
        fields = ['medicine', 'quantity', 'price', 'expiry_date']
        widgets = {
            'medicine': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 100',
                'min': '0',
                'required': True
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 5.99',
                'step': '0.01',
                'min': '0',
                'required': True
            }),
            'expiry_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
        }
        labels = {
            'medicine': 'Medicine',
            'quantity': 'Quantity',
            'price': 'Price per Unit ($)',
            'expiry_date': 'Expiry Date',
        }

    def __init__(self, *args, pharmacy=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.pharmacy = pharmacy
        # Order medicines alphabetically
        self.fields['medicine'].queryset = Medicine.objects.all().order_by('name')

    def clean(self):
        cleaned_data = super().clean()
        medicine = cleaned_data.get('medicine')
        expiry_date = cleaned_data.get('expiry_date')

        # Check if stock with same medicine and expiry date already exists for this pharmacy
        if medicine and expiry_date and self.pharmacy:
            if Stock.objects.filter(
                pharmacy=self.pharmacy,
                medicine=medicine,
                expiry_date=expiry_date
            ).exists():
                raise ValidationError(
                    f"Stock for '{medicine}' with expiry date {expiry_date} already exists. "
                    "Please update the existing stock instead."
                )

        return cleaned_data



class NewMedicineStockForm(forms.ModelForm):
    """Form for adding stock when creating a new medicine."""
    
    class Meta:
        model = Stock
        fields = ['quantity', 'price', 'expiry_date']
        widgets = {
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 100',
                'min': '0',
                'required': True
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 5.99',
                'step': '0.01',
                'min': '0',
                'required': True
            }),
            'expiry_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
        }
        labels = {
            'quantity': 'Initial Quantity',
            'price': 'Price per Unit ($)',
            'expiry_date': 'Expiry Date',
        }

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity is not None and quantity < 0:
            raise ValidationError("Quantity cannot be negative.")
        return quantity

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None and price < 0:
            raise ValidationError("Price cannot be negative.")
        return price


class StockUpdateForm(forms.ModelForm):
    """Form for updating existing stock."""
    
    class Meta:
        model = Stock
        fields = ['quantity', 'price', 'expiry_date']
        widgets = {
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'required': True
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'required': True
            }),
            'expiry_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
        }
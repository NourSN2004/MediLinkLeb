from django import forms
from django.contrib.auth import get_user_model
from .models import Medicine, Stock

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
    """Form for creating a new medicine."""
    class Meta:
        model = Medicine
        fields = ['name', 'dosage_form', 'strength', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g., Paracetamol'
            }),
            'dosage_form': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g., Tablet, Capsule, Syrup'
            }),
            'strength': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g., 500mg'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-input',
                'placeholder': 'Brief description of the medicine',
                'rows': 3
            }),
        }
    
class StockForm(forms.ModelForm):
    """Form for adding stock to a medicine."""
    medicine = forms.ModelChoiceField(
        queryset=Medicine.objects.all(),
        widget=forms.Select(attrs={'class': 'form-input'}),
        empty_label="Select a medicine"
    )
    
    class Meta:
        model = Stock
        fields = ['medicine', 'quantity', 'price', 'expiry_date']
        widgets = {
            'quantity': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Number of units',
                'min': '0'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Price per unit',
                'step': '0.01',
                'min': '0'
            }),
            'expiry_date': forms.DateInput(attrs={
                'class': 'form-input',
                'type': 'date'
            }),
        }


class NewMedicineStockForm(forms.ModelForm):
    """Form for adding stock details when creating a new medicine."""
    class Meta:
        model = Stock
        fields = ['quantity', 'price', 'expiry_date']
        widgets = {
            'quantity': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Number of units',
                'min': '0'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Price per unit',
                'step': '0.01',
                'min': '0'
            }),
            'expiry_date': forms.DateInput(attrs={
                'class': 'form-input',
                'type': 'date'
            }),
        }


class StockUpdateForm(forms.ModelForm):
    """Form for updating existing stock."""
    class Meta:
        model = Stock
        fields = ['quantity', 'price', 'expiry_date']
        widgets = {
            'quantity': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': '0'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-input',
                'step': '0.01',
                'min': '0'
            }),
            'expiry_date': forms.DateInput(attrs={
                'class': 'form-input',
                'type': 'date'
            }),
        }
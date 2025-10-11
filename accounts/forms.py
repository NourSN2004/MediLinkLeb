from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Patient, Doctor, Pharmacy

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

class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Email')
    name = forms.CharField(max_length=120, required=True, label='Full Name')
    phone_number = forms.CharField(max_length=30, required=False, label='Phone Number')

    class Meta:
        model = User
        fields = ('email', 'username', 'name', 'phone_number', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        self.user_type = kwargs.pop('user_type', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.name = self.cleaned_data['name']
        user.phone_number = self.cleaned_data.get('phone_number', '')
        
        # Set role based on user_type from session
        if self.user_type:
            user.role = self.user_type
        
        if commit:
            user.save()
            
            # Create the corresponding subtype based on role
            if user.role == User.Role.PATIENT:
                Patient.objects.create(patient_id=user)
            elif user.role == User.Role.DOCTOR:
                Doctor.objects.create(doctor_id=user)
            elif user.role == User.Role.PHARMACY:
                Pharmacy.objects.create(pharmacy_id=user)
        
        return user

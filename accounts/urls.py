from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Home
    path('', views.home_redirect, name='home_redirect'),
    
    # Signup flow
    path('signup/step1/', views.signup_step1, name='signup_step1'),
    path('signup/step2/', views.signup_step2, name='signup_step2'),
    path('verification-sent/', views.verification_sent, name='verification_sent'),
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    
    # Authentication
    path('login/', views.custom_login, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    
    # Password reset
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<str:token>/', views.reset_password, name='reset_password'),
    
    # Dashboard previews
    path('preview/doctor/', views.doctor_home_preview, name='doctor_home_preview'),
    
    # Protected pages
    path('doctor/home/', views.doctor_home, name='doctor_home'),
    path('patient/home/', views.patient_home, name='patient_home'),
    path('pharmacy/home/', views.pharmacy_home, name='pharmacy_home'),

    # Doctor appointments
    path('doctor/appointments/', views.doctor_appointments, name='doctor_appointments'),
    path('doctor/appointments/new/', views.doctor_new_appointment, name='doctor_new_appointment'),
    path('doctor/appointments/<int:appointment_id>/', views.doctor_appointment_detail, name='doctor_appointment_detail'),
    path('doctor/appointments/<int:appointment_id>/edit/', views.doctor_appointment_edit, name='doctor_appointment_edit'),
    path('doctor/appointments/<int:appointment_id>/cancel/', views.doctor_appointment_cancel, name='doctor_appointment_cancel'),
    path('doctor/appointments/<int:appointment_id>/complete/', views.doctor_appointment_complete, name='doctor_appointment_complete'),

    # Doctor patient search
    path('doctor/search/', views.doctor_patient_search, name='doctor_patient_search'),

    # Doctor full schedule calendar
    path('doctor/schedule/', views.doctor_full_schedule, name='doctor_full_schedule'),

    # Doctor availability management
    path('doctor/hours/', views.doctor_hours, name='doctor_hours'),

    # Pharmacy dashboard & management
    path('pharmacy/home/', views.pharmacy_home, name='pharmacy_home'),
    path('pharmacy/add-medicine/', views.add_medicine, name='add_medicine'),
    path('pharmacy/update-stock/', views.update_stock, name='update_stock'),
    path('pharmacy/inventory/', views.view_inventory, name='view_inventory'),
    path('pharmacy/delete-stock/<int:stock_id>/', views.delete_stock, name='delete_stock'),
    
]

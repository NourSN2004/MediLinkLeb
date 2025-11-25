"""
URL Configuration for Web Interface
"""
from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/step1/', views.signup_step1_view, name='signup_step1'),
    path('signup/step2/', views.signup_step2_view, name='signup_step2'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),

    # Doctor pages
    path('doctor/home/', views.doctor_home_view, name='doctor_home'),
    path('doctor/appointments/', views.doctor_appointments_view, name='doctor_appointments'),
    path('doctor/appointments/new/', views.doctor_new_appointment_view, name='doctor_new_appointment'),
    path('doctor/appointments/<int:appointment_id>/', views.doctor_appointment_detail_view, name='doctor_appointment_detail'),
    path('doctor/appointments/<int:appointment_id>/edit/', views.doctor_appointment_edit_view, name='doctor_appointment_edit'),
    path('doctor/appointments/<int:appointment_id>/cancel/', views.doctor_appointment_cancel_view, name='doctor_appointment_cancel'),
    path('doctor/appointments/<int:appointment_id>/complete/', views.doctor_appointment_complete_view, name='doctor_appointment_complete'),
    path('doctor/schedule/', views.doctor_full_schedule_view, name='doctor_full_schedule'),
    path('doctor/patients/', views.doctor_patient_search_view, name='doctor_patient_search'),
    path('doctor/patients/add/', views.doctor_add_patient_view, name='doctor_add_patient'),
    path('doctor/hours/', views.doctor_hours_view, name='doctor_hours'),
    path('doctor/availability/', views.doctor_availability_view, name='doctor_availability'),

    # Patient pages
    path('patient/home/', views.patient_home_view, name='patient_home'),
    path('patient/search/', views.patient_search_doctors_view, name='patient_search'),
    path('patient/search-doctors/', views.patient_search_doctors_view, name='schedule_appointment'),
    path('patient/appointments/', views.patient_appointments_view, name='view_appointments'),
    path('patient/appointments/<int:appointment_id>/cancel/', views.cancel_appointment_view, name='cancel_appointment'),
    path('patient/medical-history/', views.patient_medical_history_view, name='view_medical_history'),
    path('patient/prescriptions/', views.patient_prescriptions_view, name='view_prescriptions'),
    path('patient/browse-medicine/', views.browse_medicine_view, name='browse_medicine'),
    path('patient/doctor-availability/', views.view_doctor_availability_view, name='view_doctor_availability'),

    # Pharmacy pages
    path('pharmacy/home/', views.pharmacy_home_view, name='pharmacy_home'),
    path('pharmacy/settings/', views.pharmacy_settings_view, name='pharmacy_settings'),
    path('pharmacy/staff/<int:staff_id>/delete/', views.delete_staff_view, name='delete_pharmacist'),
    path('pharmacy/medicine/add/', views.add_medicine_view, name='add_medicine'),
    path('pharmacy/stock/update/', views.update_stock_view, name='update_stock'),
    path('pharmacy/stock/<int:stock_id>/delete/', views.delete_stock_view, name='delete_stock'),
    path('pharmacy/inventory/', views.view_inventory_view, name='view_inventory'),

    # Utility
    path('error/', views.error_view, name='error'),
]

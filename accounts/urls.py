from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Home redirect based on user role
    path('', views.home_redirect, name='home_redirect'),
    
    # Signup flow
    path('signup/step1/', views.signup_step1, name='signup_step1'),
    path('signup/step2/', views.signup_step2, name='signup_step2'),
    path('verification-sent/', views.verification_sent, name='verification_sent'),
    
    # Preview pages (for development/demo)
    path('preview/doctor/', views.doctor_home_preview, name='doctor_home_preview'),
    
    # User dashboards
    path('doctor/home/', views.doctor_home, name='doctor_home'),
    path('patient/home/', views.patient_home, name='patient_home'),

    # Authentication
    path('login/', views.custom_login, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
]

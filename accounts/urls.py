from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # signup flow
    path('', views.doctor_home_preview, name='doctor_home'),

    path('signup/step1/', views.signup_step1, name='signup_step1'),
    path('signup/step2/', views.signup_step2, name='signup_step2'),
    path('verification-sent/', views.verification_sent, name='verification_sent'),
    path('preview/doctor/', views.doctor_home_preview, name='doctor_home_preview'),
    # auth (basic)
    path('login/', auth_views.LoginView.as_view(
        template_name='accounts/login.html',
        extra_context={'title': 'Sign in'}
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]

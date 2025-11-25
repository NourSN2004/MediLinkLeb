"""
Doctor Service URL Configuration
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from .views import DoctorViewSet, DoctorWorkingHoursViewSet, DoctorTimeOffViewSet

# Main router for doctors
router = DefaultRouter()
router.register(r'', DoctorViewSet, basename='doctor')

# Nested routers for doctor-specific resources
doctors_router = routers.NestedDefaultRouter(router, r'', lookup='doctor')
doctors_router.register(r'working-hours', DoctorWorkingHoursViewSet, basename='doctor-working-hours')
doctors_router.register(r'time-off', DoctorTimeOffViewSet, basename='doctor-time-off')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(doctors_router.urls)),
]

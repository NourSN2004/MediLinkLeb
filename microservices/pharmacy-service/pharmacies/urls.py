"""
Pharmacy Service URL Configuration
Defines API endpoints for pharmacies and staff
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from .views import PharmacyViewSet, PharmacistStaffViewSet

# Main router for pharmacies
router = DefaultRouter()
router.register(r'', PharmacyViewSet, basename='pharmacy')

# Nested router for pharmacy-specific staff
pharmacies_router = routers.NestedDefaultRouter(router, r'', lookup='pharmacy')
pharmacies_router.register(r'staff', PharmacistStaffViewSet, basename='pharmacy-staff')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(pharmacies_router.urls)),
]

"""
Patient Service URL Configuration
Defines API endpoints for patients, test results, and prescriptions
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PatientViewSet,
    PatientTestResultViewSet,
    PrescriptionViewSet
)

# Main router
router = DefaultRouter()
router.register(r'', PatientViewSet, basename='patient')
router.register(r'test-results', PatientTestResultViewSet, basename='test-result')
router.register(r'prescriptions', PrescriptionViewSet, basename='prescription')

urlpatterns = [
    path('', include(router.urls)),
]

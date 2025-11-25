"""
Scheduling Service URL Configuration
Defines API endpoints for appointments and notes
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AppointmentViewSet, AppointmentNoteViewSet

# Main router
router = DefaultRouter()
router.register(r'', AppointmentViewSet, basename='appointment')
router.register(r'notes', AppointmentNoteViewSet, basename='appointment-note')

urlpatterns = [
    path('', include(router.urls)),
]

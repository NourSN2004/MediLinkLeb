"""
Health check endpoints for Kubernetes probes
"""
from django.urls import path
from .views import HealthCheckView, ReadinessCheckView

urlpatterns = [
    path('live/', HealthCheckView.as_view(), name='health-live'),
    path('ready/', ReadinessCheckView.as_view(), name='health-ready'),
]

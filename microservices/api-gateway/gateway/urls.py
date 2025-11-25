"""
Main URL Configuration for API Gateway
Handles both web interface and API proxying
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.conf.urls.static import static


@require_http_methods(["GET"])
def health_check(request):
    """Health check endpoint"""
    return JsonResponse({'status': 'healthy'})


urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Health check
    path('health/', health_check),

    # Web interface (HTML pages)
    path('', include('web.urls')),

    # API endpoints - these could proxy to microservices if needed
    # For now, applications can call microservices directly or through the gateway
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/pharmacies/', include('pharmacies.urls')),
    path('health/', include('pharmacies.health_urls')),
]

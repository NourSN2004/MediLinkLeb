from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/scheduling/', include('scheduling.urls')),
    path('health/', include('scheduling.health_urls')),
]

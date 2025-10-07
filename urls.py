from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),  # routes for signup + auth
    path('', include('accounts.urls_root')),     # doctor home at "/"
]

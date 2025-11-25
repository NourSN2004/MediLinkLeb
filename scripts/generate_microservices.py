#!/usr/bin/env python3
"""
Script to generate boilerplate for MediLink microservices
"""
import os
from pathlib import Path

MICROSERVICES_DIR = Path(__file__).parent.parent / "microservices"

# Service configurations
SERVICES = {
    "doctor-service": {
        "port": 8002,
        "app_name": "doctors",
        "models": ["Doctor", "DoctorWorkingHours", "DoctorTimeOff"]
    },
    "patient-service": {
        "port": 8003,
        "app_name": "patients",
        "models": ["Patient", "PatientTestResult"]
    },
    "pharmacy-service": {
        "port": 8004,
        "app_name": "pharmacies",
        "models": ["Pharmacy", "PharmacistStaff"]
    },
    "scheduling-service": {
        "port": 8005,
        "app_name": "scheduling",
        "models": ["Appointment"]
    },
    "inventory-service": {
        "port": 8006,
        "app_name": "inventory",
        "models": ["Medicine", "Stock", "Prescribes"]
    },
    "notification-service": {
        "port": 8007,
        "app_name": "notifications",
        "models": ["Notification"]
    }
}

REQUIREMENTS_TEMPLATE = """Django>=4.2,<5.0
djangorestframework>=3.14.0
djangorestframework-simplejwt>=5.3.0
psycopg2-binary>=2.9.9
python-decouple>=3.8
gunicorn>=21.2.0
django-cors-headers>=4.3.0
requests>=2.31.0
"""

MANAGE_PY_TEMPLATE = """#!/usr/bin/env python
import os
import sys

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', '{service_module}.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
"""

SETTINGS_TEMPLATE = """from pathlib import Path
from decouple import config
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-dev-key')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='*').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    '{app_name}',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = '{service_module}.urls'

TEMPLATES = [
    {{
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {{
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        }},
    }},
]

WSGI_APPLICATION = '{service_module}.wsgi.application'

DATABASES = {{
    'default': {{
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='medilink_db'),
        'USER': config('DB_USER', default='medilink'),
        'PASSWORD': config('DB_PASSWORD', default='medilink_password'),
        'HOST': config('DB_HOST', default='postgres-service'),
        'PORT': config('DB_PORT', default='5432'),
    }}
}}

AUTH_PASSWORD_VALIDATORS = [
    {{'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'}},
    {{'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'}},
    {{'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'}},
    {{'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'}},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Beirut'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {{
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
}}

SIMPLE_JWT = {{
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=24),
    'SIGNING_KEY': config('JWT_SECRET_KEY', default=SECRET_KEY),
    'AUTH_HEADER_TYPES': ('Bearer',),
}}

CORS_ALLOW_ALL_ORIGINS = config('CORS_ALLOW_ALL', default=True, cast=bool)

SERVICE_SECRET_KEY = config('SERVICE_SECRET_KEY', default='service-secret')

# Service URLs for inter-service communication
AUTH_SERVICE_URL = config('AUTH_SERVICE_URL', default='http://auth-service:8001')
DOCTOR_SERVICE_URL = config('DOCTOR_SERVICE_URL', default='http://doctor-service:8002')
PATIENT_SERVICE_URL = config('PATIENT_SERVICE_URL', default='http://patient-service:8003')
PHARMACY_SERVICE_URL = config('PHARMACY_SERVICE_URL', default='http://pharmacy-service:8004')
SCHEDULING_SERVICE_URL = config('SCHEDULING_SERVICE_URL', default='http://scheduling-service:8005')
INVENTORY_SERVICE_URL = config('INVENTORY_SERVICE_URL', default='http://inventory-service:8006')
NOTIFICATION_SERVICE_URL = config('NOTIFICATION_SERVICE_URL', default='http://notification-service:8007')
"""

URLS_TEMPLATE = """from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/{api_path}/', include('{app_name}.urls')),
    path('health/', include('{app_name}.health_urls')),
]
"""

WSGI_TEMPLATE = """import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', '{service_module}.settings')
application = get_wsgi_application()
"""

HEALTH_URLS_TEMPLATE = """from django.urls import path
from .views import HealthCheckView, ReadinessCheckView

urlpatterns = [
    path('live/', HealthCheckView.as_view(), name='health-live'),
    path('ready/', ReadinessCheckView.as_view(), name='health-ready'),
]
"""

HEALTH_VIEWS_TEMPLATE = """from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.db import connection

class HealthCheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({{'status': 'healthy'}}, status=status.HTTP_200_OK)

class ReadinessCheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            connection.ensure_connection()
            return Response({{'status': 'ready'}}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {{'status': 'not ready', 'error': str(e)}},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
"""

DOCKERFILE_TEMPLATE = """FROM python:3.12-slim as builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \\
    build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \\
    libpq5 && rm -rf /var/lib/apt/lists/*

COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

COPY . .
RUN mkdir -p staticfiles

EXPOSE {port}

ENV PYTHONUNBUFFERED=1 \\
    DJANGO_SETTINGS_MODULE={service_module}.settings

CMD python manage.py migrate --no-input && \\
    python manage.py collectstatic --no-input && \\
    gunicorn {service_module}.wsgi:application --bind 0.0.0.0:{port} --workers 4 --timeout 120
"""

ENV_EXAMPLE_TEMPLATE = """# Django Settings
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
DEBUG=False
ALLOWED_HOSTS=*

# Database Configuration
DB_NAME=medilink_db
DB_USER=medilink
DB_PASSWORD=medilink_password
DB_HOST=postgres-service
DB_PORT=5432

# Service-to-Service Authentication
SERVICE_SECRET_KEY=service-secret-change-in-production

# CORS Settings
CORS_ALLOW_ALL=True

# Service URLs
AUTH_SERVICE_URL=http://auth-service:8001
DOCTOR_SERVICE_URL=http://doctor-service:8002
PATIENT_SERVICE_URL=http://patient-service:8003
PHARMACY_SERVICE_URL=http://pharmacy-service:8004
SCHEDULING_SERVICE_URL=http://scheduling-service:8005
INVENTORY_SERVICE_URL=http://inventory-service:8006
NOTIFICATION_SERVICE_URL=http://notification-service:8007
"""

def create_file(path, content):
    """Create a file with content"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    print(f"Created: {path}")

def generate_service(service_name, config):
    """Generate a microservice with boilerplate"""
    service_dir = MICROSERVICES_DIR / service_name
    service_module = service_name.replace('-', '_')
    app_name = config['app_name']
    port = config['port']
    api_path = app_name

    print(f"\n=== Generating {service_name} ===")

    # Create service module directory
    service_module_dir = service_dir / service_module
    app_dir = service_dir / app_name
    migrations_dir = app_dir / "migrations"

    # Create __init__.py files
    create_file(service_module_dir / "__init__.py", f"# {service_name}")
    create_file(app_dir / "__init__.py", f"# {app_name}")
    create_file(migrations_dir / "__init__.py", "# Migrations")

    # Create requirements.txt
    create_file(service_dir / "requirements.txt", REQUIREMENTS_TEMPLATE)

    # Create manage.py
    manage_content = MANAGE_PY_TEMPLATE.format(service_module=service_module)
    create_file(service_dir / "manage.py", manage_content)
    os.chmod(service_dir / "manage.py", 0o755)

    # Create settings.py
    settings_content = SETTINGS_TEMPLATE.format(
        service_module=service_module,
        app_name=app_name
    )
    create_file(service_module_dir / "settings.py", settings_content)

    # Create urls.py
    urls_content = URLS_TEMPLATE.format(
        api_path=api_path,
        app_name=app_name
    )
    create_file(service_module_dir / "urls.py", urls_content)

    # Create wsgi.py
    wsgi_content = WSGI_TEMPLATE.format(service_module=service_module)
    create_file(service_module_dir / "wsgi.py", wsgi_content)

    # Create app files
    create_file(app_dir / "apps.py", f"""from django.apps import AppConfig

class {app_name.capitalize()}Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = '{app_name}'
""")

    create_file(app_dir / "admin.py", "from django.contrib import admin\n\n# Register your models here.\n")
    create_file(app_dir / "models.py", "from django.db import models\n\n# Create your models here.\n")
    create_file(app_dir / "serializers.py", "from rest_framework import serializers\n\n# Create your serializers here.\n")
    create_file(app_dir / "views.py", HEALTH_VIEWS_TEMPLATE)
    create_file(app_dir / "urls.py", "from django.urls import path\n\nurlpatterns = [\n    # Add your API endpoints here\n]\n")
    create_file(app_dir / "health_urls.py", HEALTH_URLS_TEMPLATE)

    # Create Dockerfile
    dockerfile_content = DOCKERFILE_TEMPLATE.format(
        service_module=service_module,
        port=port
    )
    create_file(service_dir / "Dockerfile", dockerfile_content)

    # Create .env.example
    create_file(service_dir / ".env.example", ENV_EXAMPLE_TEMPLATE)

    print(f"✓ {service_name} generated successfully")

def main():
    """Generate all microservices"""
    print("Starting microservice generation...")

    for service_name, config in SERVICES.items():
        generate_service(service_name, config)

    print("\n" + "="*50)
    print("All microservices generated successfully!")
    print("="*50)

if __name__ == "__main__":
    main()

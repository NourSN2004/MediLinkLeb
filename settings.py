from pathlib import Path
from os import getenv
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ------------------------------------------------
# BASE SETUP
# ------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent

SECRET_KEY = "dev-secret-key-change-this"
DEBUG = True
ALLOWED_HOSTS = []


# ------------------------------------------------
# APPLICATIONS
# ------------------------------------------------
INSTALLED_APPS = [
    # Django built-ins
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Your app
    "accounts",
]


# ------------------------------------------------
# MIDDLEWARE
# ------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# ------------------------------------------------
# URLS / WSGI
# ------------------------------------------------
ROOT_URLCONF = "urls"  # since your urls.py is at project root
WSGI_APPLICATION = "wsgi.application"  # optional; Django ignores if not used


# ------------------------------------------------
# TEMPLATES
# ------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],  # app templates are automatically found
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# ------------------------------------------------
# DATABASE
# ------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# ------------------------------------------------
# PASSWORD VALIDATION
# ------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# ------------------------------------------------
# INTERNATIONALIZATION
# ------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Beirut"
USE_I18N = True
USE_TZ = True


# ------------------------------------------------
# STATIC FILES
# ------------------------------------------------
STATIC_URL = "static/"
STATICFILES_DIRS = [
    BASE_DIR / "accounts" / "static",
]


# ------------------------------------------------
# AUTH REDIRECTS
# ------------------------------------------------
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "doctor_home"
LOGOUT_REDIRECT_URL = "login"


# ------------------------------------------------
# DEFAULTS
# ------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"



# -----------------------------
# MEDIA CONFIGURATION
# -----------------------------
import os

MEDIA_URL = '/media/'  # URL prefix for accessing uploaded files
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')  # Actual folder where uploads will be stored




AUTH_USER_MODEL = 'accounts.User'

# ==============================================================================
# EMAIL CONFIGURATION
# ==============================================================================

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = getenv('EMAIL_HOST_USER') # ← Replace with YOUR Gmail
EMAIL_HOST_PASSWORD = getenv('APP_PASS')  # ← Replace with YOUR App Password (16 chars)
DEFAULT_FROM_EMAIL = f'MediLink <{EMAIL_HOST_USER}>'  # ← Replace with YOUR Gmail
SITE_URL = 'http://localhost:8000'  # Keep this as is for local development
EMAIL_TIMEOUT = 10
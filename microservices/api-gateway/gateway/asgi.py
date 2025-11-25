"""
ASGI config for API Gateway
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gateway.settings')

application = get_asgi_application()

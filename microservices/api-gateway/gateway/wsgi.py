"""
WSGI config for API Gateway
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gateway.settings')

application = get_wsgi_application()

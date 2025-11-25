# wsgi.py
import os
from django.core.wsgi import get_wsgi_application

# our settings module sits next to this file
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

application = get_wsgi_application()

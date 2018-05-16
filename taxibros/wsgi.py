"""
WSGI config for taxibros project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/howto/deployment/wsgi/
"""

import os
import dotenv

from django.core.wsgi import get_wsgi_application

dotenv.read_dotenv(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "taxibros.settings.development")

application = get_wsgi_application()

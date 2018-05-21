"""
WSGI config for taxibros project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/howto/deployment/wsgi/
"""

import os
import dotenv
from daemons.download import start_download
import subprocess
from django.core.wsgi import get_wsgi_application

dotenv.read_dotenv(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "taxibros.settings.development")

application = get_wsgi_application()
#HACK: Runs the cron job here as wsgi.py is ran only once on server start-up
#Ensures that there is only one instance of the task
# Download JSON stream.
start_download(repeat=60, repeat_until=None)
#Runs the subprocess asynchronously in the background
cmd = ['python3', 'manage.py', 'process_tasks', '--queue', 'taxi-availability']
subprocess.Popen(cmd)

"""
WSGI config for taxibros project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/howto/deployment/wsgi/
"""

import os
import dotenv
import subprocess
import psutil

from daemons.download import start_download, process_location_coordinates
from django.core.wsgi import get_wsgi_application
from django.conf import settings


# Reading .env file
dotenv.read_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "taxibros.settings.local_settings")
application = get_wsgi_application()

if settings.DAEMON_START:
    # HACK: Runs the cron job here as wsgi.py is ran only once on server start-up
    # Ensures that there is only one instance of the task
    # Download JSON stream.
    start_download(repeat=60, repeat_until=None)

    # Runs the subprocess asynchronously in the background
    # Runs only if no command already running.
    cmd = ["python3", "manage.py", "process_tasks", "--queue", "taxi-availability"]
    for pid in psutil.pids():
        p = psutil.Process(pid)
        if p.cmdline() == cmd:
            break
    else:
        subprocess.Popen(cmd)
if settings.UPDATE_ROADS and not settings.DAEMON_START:
    process_location_coordinates()

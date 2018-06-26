"""
WSGI config for taxibros project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/howto/deployment/wsgi/
"""

import dotenv
import json
import os
import psutil
import requests
import subprocess
import time

from background_task.models import Task
from daemons.convert import process_location_coordinates, ConvertRoad
from daemons.download import start_download
from daemons.grid_coordinates import GridCoordinates
from django.core.wsgi import get_wsgi_application
from django.conf import settings

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")

# Read .env file.
dotenv.load_dotenv(dotenv_path=dotenv_path)

# If expired keys, update .env file, read .env file again.
if not settings.ONEMAP_EXPIRY_TIMESTAMP or time.time() > int(
    settings.ONEMAP_EXPIRY_TIMESTAMP
):
    print("Fetching new OneMap token")
    payload = {"email": settings.ONEMAP_EMAIL, "password": settings.ONEMAP_PASSWORD}
    request = requests.post(
        "https://developers.onemap.sg/privateapi/auth/post/getToken",
        data=json.dumps(payload),
        headers={"Content-Type": "application/json"},
    )
    request_json = request.json()
    dotenv.set_key(dotenv_path, "ONEMAP_SECRET_KEY", request_json["access_token"])
    dotenv.set_key(
        dotenv_path, "ONEMAP_EXPIRY_TIMESTAMP", request_json["expiry_timestamp"]
    )
    dotenv.load_dotenv(dotenv_path=dotenv_path)
else:
    print("Using old OneMap token")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "taxibros.settings.local_settings")
application = get_wsgi_application()

if settings.DAEMON_START:

    # Delete all previous tasks before running current tasks.
    Task.objects.all().delete()

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
    if settings.GRID_CLOSEST_ROADS:
        ConvertRoad().convert(
            GridCoordinates().interpolate(
                ll_lat=settings.GRID_LL_LAT,
                ll_lng=settings.GRID_LL_LNG,
                ur_lat=settings.GRID_UR_LAT,
                ur_lng=settings.GRID_UR_LNG,
            )
        )
    else:
        process_location_coordinates()

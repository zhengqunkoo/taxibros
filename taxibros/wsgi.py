"""
WSGI config for taxibros project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/howto/deployment/wsgi/
"""

import codecs
import dotenv
import fileinput
import json
import os
import psutil
import requests
import subprocess
import time

from background_task.models import Task
from daemons.convert import ConvertLocation
from daemons.download import start_download
from daemons.models import Location
from daemons.grid_coordinates import GridCoordinates
from django.core.wsgi import get_wsgi_application
from django.conf import settings

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")


def dotenv_parse_line(line):
    line = line.strip()

    # Ignore lines with `#` or which doesn't have `=` in it.
    if not line or line.startswith("#") or "=" not in line:
        return None, None

    k, v = line.split("=", 1)

    if k.startswith("export "):
        k = k.lstrip("export ")

    # Remove any leading and trailing spaces in key, value
    k, v = k.strip(), v.strip()

    if v:
        v = v.encode("unicode-escape").decode("ascii")
        quoted = v[0] == v[-1] in ['"', "'"]
        if quoted:
            v = codecs.getdecoder("unicode_escape")(v[1:-1])[0]

    return k, v


def dotenv_set_key(dotenv_path, key_to_set, value_to_set, quote_mode="always"):
    """
    Adds or Updates a key/value to the given .env

    If the .env path given doesn't exist, fails instead of risking creating
    an orphan .env somewhere in the filesystem
    """
    value_to_set = value_to_set.strip("'").strip('"')
    if not os.path.exists(dotenv_path):
        warnings.warn("can't write to %s - it doesn't exist." % dotenv_path)
        return None, key_to_set, value_to_set

    if " " in value_to_set:
        quote_mode = "always"

    # Add newlines to end of template.
    line_template = '{}="{}"\n' if quote_mode == "always" else "{}={}\n"
    line_out = line_template.format(key_to_set, value_to_set)

    replaced = False
    for line in fileinput.input(dotenv_path, inplace=True):
        k, v = dotenv_parse_line(line)
        if k == key_to_set:
            replaced = True
            line = line_out
        print(line, end="")

    if not replaced:
        with io.open(dotenv_path, "a") as f:
            f.write("{}\n".format(line_out))

    return True, key_to_set, value_to_set


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
    dotenv_set_key(dotenv_path, "ONEMAP_SECRET_KEY", request_json["access_token"])
    dotenv_set_key(
        dotenv_path, "ONEMAP_EXPIRY_TIMESTAMP", request_json["expiry_timestamp"]
    )
    dotenv.load_dotenv(dotenv_path=dotenv_path, override=True)
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


if settings.INITIALIZE_LOCATIONS and not settings.DAEMON_START:
    for location in Location.objects.filter(lat=0, lng=0):
        ConvertLocation().store_location_data(location.roadID)

    if settings.GRID_CLOSEST_ROADS:
        ConvertLocation().store_locations(
            GridCoordinates().interpolate(
                ll_lat=settings.GRID_LL_LAT,
                ll_lng=settings.GRID_LL_LNG,
                ur_lat=settings.GRID_UR_LAT,
                ur_lng=settings.GRID_UR_LNG,
            )
        )

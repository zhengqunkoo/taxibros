#!/usr/bin/env python3

"""Inserts BSON files with timestamps as filenames, into django's sqlite db.
@param path: path to folder that contains all BSON files.
    Assume no other files in folder.
"""
import bson
import sys
import os
import dotenv
import django
from django.db import models


if __name__ == '__main__':  
    dotenv.read_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "taxibros.settings.local_settings")
    django.setup()
    from taxibros.wsgi import application
    from daemons.models import Timestamp, Coordinate

    _, path = sys.argv
    # Filename is date_time.
    for date_time in [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]:
        print(date_time)
        with open(os.path.join(path, date_time), 'rb') as f:
            timestamp = Timestamp(date_time=date_time)
            timestamp.save()
            json = bson.loads(f.read())
            for coordinate in json['geometry']['coordinates']:
                Coordinate(
                    lat=coordinate[1],
                    long=coordinate[0],
                    timestamp=timestamp,
                ).save()

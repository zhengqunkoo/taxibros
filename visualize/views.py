from django.shortcuts import render
from daemons.models import Coordinate, Timestamp
from background_task.models import Task
from django.utils import timezone
from itertools import chain
import datetime
import os

def index(request):
    """View function for home page of site."""
    #CHECK1:If daemon is running
    if (Task.objects.all().count()==0):
        return render(
            request,
            'visualize/index.html',
            {"api_key":os.getenv("GOOGLEMAPS_SECRET_KEY"), "error_message": "Im sorry. The service appears to be experiencing a malfunction."}
        )
    #CHECK2:If there is insufficient data
    times = Timestamp.objects.filter(date_and_time__range = [timezone.now() - datetime.timedelta(minutes=5), timezone.now()])
    if (times.count()<5):
        return render(
            request,
            'visualize/index.html',
            {"api_key":os.getenv("GOOGLEMAPS_SECRET_KEY"), "error_message": "Data is still incomplete, please wait a few minutes before refreshing."}
        )

    return render(
        request,
        'visualize/index.html',
        {"api_key":os.getenv("GOOGLEMAPS_SECRET_KEY")}
    )
def genjs(request):
    # Render the js template index.html with the data in the context variable.
    # Filters with a 5 minute timespan
    times = Timestamp.objects.filter(date_and_time__range = [timezone.now() - datetime.timedelta(minutes=5), timezone.now()])

    coordinates = []
    for time in times:
        coordinates = chain(time.coordinate_set.all(), coordinates)
    context = {'coordinates':coordinates}

    return render(
            request,
            'visualize/maps.js',
            context
            )

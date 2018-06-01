import datetime

from background_task.models import Task
from daemons.models import Coordinate, Timestamp
from daemons.views import (
    get_coordinates_time,
    get_coordinates_location,
    serialize_coordinates,
)
from django.shortcuts import render
from django.utils import timezone
from django.conf import settings
from django.http import JsonResponse
from visualize.convert import ConvertHeatmap


def index(request):
    """View function for home page of site."""
    context = {
        "GOOGLEMAPS_SECRET_KEY": settings.GOOGLEMAPS_SECRET_KEY,
        "SLIDE_EVENT": settings.SLIDE_EVENT,
    }

    # CHECK1:If daemon is running
    if Task.objects.all().count() == 0:
        context[
            "error_message"
        ] = "No daemons running. Please run server once with DAEMON_START=True."
        return render(request, "visualize/index.html", context)

    # CHECK2:If there is insufficient data
    times = Timestamp.objects.filter(
        date_time__range=[
            timezone.now() - datetime.timedelta(minutes=5),
            timezone.now(),
        ]
    )
    if times.count() < 5:
        context[
            "error_message"
        ] = "Data is still incomplete, please wait a few minutes before refreshing."
        return render(request, "visualize/index.html", context)

    # Else: render with normal context.
    return render(request, "visualize/index.html", context)


def gen_time_js(request):
    """Return Json of serialized list of coordinates according to time."""
    return JsonResponse(
        {"coordinates": serialize_coordinates(get_coordinates_time(request))}
    )


def gen_loc_js(request):
    """Return Json of serialized list of coordinates, average distance away, and number of taxis according to the location"""
    coords, average, number, day_stats = get_coordinates_location(request)
    return JsonResponse(
        {
            "coordinates": serialize_coordinates(coords),
            "average_dist": average,
            "number": number,
            "day_stats": day_stats,
        }
    )


def map_js(request):
    """Render Javascript file with list of coordinates in context."""
    return render(
        request, "visualize/map.js", {"coordinates": get_coordinates_time(request)}
    )


# TODO debug
def heatmap(request):
    """Convert one minute of coordinates into heatmap."""
    ch = ConvertHeatmap()
    ch._date_time_end = ch._date_time_start + datetime.timedelta(minutes=1)
    ch.store()
    return render(request, "visualize/index.html", {"coordinates": []})

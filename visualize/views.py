import datetime

from background_task.models import Task
from daemons.models import Coordinate, Timestamp
from daemons.views import get_coordinates_time, get_coordinates_location
from django.shortcuts import render
from django.utils import timezone
from django.conf import settings
from django.http import JsonResponse
from visualize.heatmap_slider import HeatmapSlider


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


def gen_heatmap_js(request):
    """Return Json of intensity, coords, and timestamp of heat tile."""
    coordinates = Timestamp.objects.latest("date_time").coordinate_set.all()
    hs = HeatmapSlider(serialize_coordinates(coordinates))
    try:
        hs.show()
    except:
        pass
    intensities, xs, ys, timestamp = get_heatmap_time(request)
    return JsonResponse(
        {
            "intensities": intensities,
            "xs": xs,
            "ys": ys,
            "timestamp": timestamp.date_time,
        }
    )


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


def get_heatmap_time(request):
    """Filter range one minute long, ensures at least one date_time returned.
    If two date_times returned, select most recent one.
    @param request: HTTP GET request containing other variables.
        minutes:
            predict taxi locations at this amount of time into the future.
            default: 0 (meaning now).
    @return list of heatmaps.
    """
    minutes = request.GET.get("minutes")
    if minutes == None:
        minutes = 0

    # If true, minutes=0 means current time.
    # If false, minutes=0 means time of latest timestamp.
    if settings.HEATMAP_NOW:
        now = datetime.datetime.now(pytz.utc)
    else:
        now = Timestamp.objects.latest("date_time").date_time

    start_window = datetime.timedelta(minutes=int(minutes) + 1)
    end_window = datetime.timedelta(minutes=int(minutes))
    times = Timestamp.objects.filter(
        date_time__range=(now - start_window, now - end_window)
    )

    # If no times, return empty list.
    heatmaps = []
    if times:
        # If many times, Select most recent time.
        time = times[0]
        heatmaps = time.heatmap_set.all()
    intensities = [heatmap.intensity for heatmap in heatmaps]
    xs = [heatmap.x for heatmap in heatmaps]
    ys = [heatmap.y for heatmap in heatmaps]
    return intensities, xs, ys, time


def serialize_coordinates(coordinates):
    """Helper function to serialize list to output as needed in JsonResponse.
    @return serialized list of coordinates.
    """
    return [[float(c.lat), float(c.long)] for c in coordinates]

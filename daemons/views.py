import datetime
import pytz
import math
import json

from .models import Timestamp, Coordinate
from django.shortcuts import render
from django.conf import settings


def index(request):
    """View function for home page of site."""

    # Count objects.
    num_timestamps = Timestamp.objects.count()
    num_coordinates = Coordinate.objects.count()

    # Render the HTML template index.html with the data in the context variable.
    return render(
        request,
        "daemons/index.html",
        context={"num_timestamps": num_timestamps, "num_coordinates": num_coordinates},
    )


def get_coordinates_time(request):
    """Filter range one minute long, ensures at least one date_time returned.
    If two date_times returned, select most recent one.
    @param request: HTTP GET request containing other variables.
        minutes:
            predict taxi locations at this amount of time into the future.
            default: 0 (meaning now).
    @return list of coordinates.
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
    coordinates = []
    if times:
        # If many times, Select most recent time.
        time = times[0]
        coordinates = time.coordinate_set.all()
    return coordinates


def get_coordinates_location(request):
    """@return coords, average_dist away of cars within 500m radius, num cars within 500m radius"""
    pos = request.GET.get("pos")
    pos = json.loads(pos)
    distFunc = lambda x: math.pow(
        math.pow(110570 * (float(x.lat) - pos["lat"]), 2)
        + math.pow(111320 * (float(x.long) - pos["lng"]), 2),
        0.5,
    )

    # Approximating lat/long
    # http://www.longitudestore.com/how-big-is-one-gps-degree.html

    # Assumption: position passes on the coordinates
    now = Timestamp.objects.latest("date_time")
    coords = now.coordinate_set.all()

    result = []
    total_dist = 0
    num = 0
    for coord in coords:
        dist = distFunc(coord)
        if dist < 500:
            result.append(coord)
            num += 1
            total_dist += dist

    # timezone.activate(pytz.timezone(settings.TIME_ZONE))
    date_time_end = Timestamp.objects.latest("date_time").date_time
    # TODO: Uncomment below. Currently this way cause not enough data
    # date_time_end = timezone.localtime(date_time_end)
    date_time_end = date_time_end.replace(hour=0, minute=0, second=0)
    date_time_start = date_time_end - datetime.timedelta(days=1)

    # Generating the coordinates in 10min intervals for yesterday's time
    timestamps = Timestamp.objects.filter(
        date_time__range=(date_time_start, date_time_end)
    )

    timestamps = filter(
        lambda time: ((time.date_time.replace(second=0) - date_time_start).seconds)
        % 300
        == 0,
        timestamps,
    )

    day_stats = []
    for time in timestamps:
        coords = time.coordinate_set.all()
        num_at_time = 0
        for coord in coords:
            dist = distFunc(coord)
            if dist < 500:
                num_at_time += 1
        day_stats.append(num_at_time)

    return result, total_dist / num if num != 0 else 0, num, day_stats


def serialize_coordinates(coordinates):
    """Helper function to serialize list to output as needed in JsonResponse.
    @return serialized list of coordinates.
    """
    return [[float(c.lat), float(c.long)] for c in coordinates]

import datetime
import pytz
import math
import json
import requests

from .download import start_download
from .models import Timestamp, Coordinate, Location, LocationRecord
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

    best_road = get_best_road(coords)

    # TODO: Refactor code to draw general graph time
    """
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
        """
    return result, total_dist / num if num != 0 else 0, num, best_road


def get_best_road(coordinates):
    """Returns the road with the largest number of taxis in db
    @param: coordinates of taxis within 500m
    """
    roads = get_closest_roads(coordinates)
    max_val = 0
    max_road = None
    for road in get_closest_roads:
        val = get_count_at_road(road)
        if val > max_val:
            max_val = val
            max_road = road
    return max_road


def get_count_at_road(roadID):
    loc = Location.objects.filter(location=roadID)[0]
    records = loc.locationrecord_set.all()
    return sum(map(lambda rec: rec.count, records))


def get_closest_roads(coordinates):
    """Retrieves the closest road segments to the coordinates
    @param: coordinates of the taxis
    @return: road segments of coordinates"""
    coords_params = "|".join(
        [str(coordinate[1]) + "," + str(coordinate[0]) for coordinate in coordinates]
    )
    url = (
        "https://roads.googleapis.com/v1/nearestRoads?points="
        + coords_params
        + "&key="
        + settings.GOOGLEMAPS_SECRET_KEY
    )
    json_val = resquests.get(url).json()
    result = [point["placeId"] for point in json_val["snappedPoints"]]

    return set(result)


def serialize_coordinates(coordinates):
    """Helper function to serialize list to output as needed in JsonResponse.
    @return serialized list of coordinates.
    """
    return [[float(c.lat), float(c.long)] for c in coordinates]

import datetime
import pytz
import math
import requests

from .convert import ConvertHeatmap
from .download import start_download
from .models import Timestamp, Coordinate, Location, LocationRecord
from django.conf import settings
from django.db import OperationalError
from django.shortcuts import render
from scipy.sparse import coo_matrix
from scipy.spatial import KDTree


# Approximating lat/lng
# http://www.longitudestore.com/how-big-is-one-gps-degree.html
M_PER_LAT = 110570
M_PER_LONG = 111320

# Set up KDTree once on server start.
import sys

sys.setrecursionlimit(30000)
try:
    locs = [loc for loc in Location.objects.all()]
    locs = list(filter(lambda x: x.lat != 0, locs))
    if len(locs) > 0:  # Tests initialize kdtree with no values
        tree = KDTree(
            list(map(lambda x: (float(x.lat), float(x.lng)), locs)), leafsize=3000
        )
        print("Successfully populated KDTree.")
    else:
        tree = KDTree([[], []])
        print("Initialized empty KDTree, due to locs empty.")
except OperationalError as e:
    print("Error accessing daemons_location, see: {}.".format(e))
    locs = []
    tree = KDTree([[], []])
else:
    print("Successfully populated locs and tree.")


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


def get_timestamp(request):
    """Retrieve one timestamp based on request time and local_settings.
    @param request: HTTP GET request containing other variables.
        minutes:
            predict taxi locations at this amount of time into the future.
            default: 0 (meaning now).
    @return Timestamp if exists, else None.
    """
    minutes = request.GET.get("minutes")
    if minutes == None:
        minutes = 0
    else:
        minutes = int(minutes)

    # If true, minutes=0 means current time.
    # If false, minutes=0 means time of latest timestamp.
    if settings.HEATMAP_NOW:
        now = datetime.datetime.now(pytz.utc)
    else:
        now = Timestamp.objects.latest("date_time").date_time

    start_window = datetime.timedelta(minutes=minutes + 1)
    end_window = datetime.timedelta(minutes=minutes)
    times = Timestamp.objects.filter(
        date_time__range=(now - start_window, now - end_window)
    )

    if not times:
        return None
    else:
        return times[0]


def get_coordinates_time(request):
    """Filter range one minute long, ensures at least one date_time returned.
    If two date_times returned, select most recent one.
    @param request: HTTP GET request containing other variables.
        minutes:
            predict taxi locations at this amount of time into the future.
            default: 0 (meaning now).
    @return list of coordinates.
    """
    # If no time, return empty list.
    coordinates = []
    time = get_timestamp(request)
    if time != None:
        coordinates = time.coordinate_set.all()
    return coordinates


def get_coordinates_location(request):
    """
    @param request: HTTP GET request containing other variables.
        lat, lng: position of client
        radius: how far client is willing to walk to hail a taxi
        minutes:
            predict taxi locations at this amount of time into the future.
            default: 0 (meaning now).
    @return tuple of:
        Many taxi information:
            coords of taxis
            total dist away of cars within radius
            num cars within radius
        Recommended taxi to hail information:
            road name of road that taxi is on
            coordinates of that road
            walking path towards that road
    """
    lat = float(request.GET.get("lat"))
    lng = float(request.GET.get("lng"))
    radius = float(request.GET.get("radius"))
    distFunc = lambda x: math.pow(
        math.pow(M_PER_LAT * (float(x.lat) - lat), 2)
        + math.pow(M_PER_LONG * (float(x.lng) - lng), 2),
        0.5,
    )

    time = get_timestamp(request)

    result = []
    total_dist = 0
    num = 0
    best_road = get_best_road(lat, lng, radius)
    road_name = None
    best_lat = None
    best_lng = None
    path_geom = None

    if time != None:
        coords = time.coordinate_set.all()
        for coord in coords:
            dist = distFunc(coord)
            if dist < radius:
                result.append(coord)
                num += 1
                total_dist += dist
        path_time = None
        path_dist = None
        if best_road != None:
            best_lat = float(best_road.lat)
            best_lng = float(best_road.lng)
            path_geom, path_time, path_dist = get_path_data(
                lat, lng, best_lat, best_lng
            )
            road_name = best_road.road_name

    return (
        result,
        total_dist,
        num,
        road_name,
        best_lat,
        best_lng,
        path_geom,
        path_time,
        path_dist,
    )


def get_heatmap_time(request):
    """Filter range one minute long, ensures at least one date_time returned.
    If two date_times returned, select most recent one.
    @param request: HTTP GET request containing other variables.
        minutes:
            predict taxi locations at this amount of time into the future.
            default: 0 (meaning now).
    @return
        If timestamp exists:
            List of heattiles, each with intensity, x-coord, and y-coord.
            Timestamp.
        Else:
            Empty list.
            None.
    """
    time = get_timestamp(request)
    if time != None:
        coo, left, right, bottom, top, xbins, ybins = ConvertHeatmap.retrieve_heatmap(
            time
        )

        # Positive for countries above equator and to right of Greenwich.
        width, height = right - left, top - bottom

        heatmap = coo.toarray()
        coo = coo_matrix(heatmap.astype(int))
        data = coo.data.tolist()
        row = coo.row.tolist()
        col = coo.col.tolist()
        xs = [round(left + width * n / xbins, 6) for n in row]
        ys = [round(bottom + height * n / ybins, 6) for n in col]
        heattiles = list(zip(data, xs, ys))
        return heattiles, time
    else:
        return [], None


def get_path_data(start_lat, start_lng, end_lat, end_lng):
    """
    @param start and end coordinates. lat, lng: position in coordinates.
    @return route_geometry: walking path from start to end.
    """
    url = "https://developers.onemap.sg/privateapi/routingsvc/route"
    params = {
        "start": "{},{}".format(start_lat, start_lng),
        "end": "{},{}".format(end_lat, end_lng),
        "routeType": "walk",
        "token": settings.ONEMAP_SECRET_KEY,
    }
    r = requests.get(url, params=params)
    if r.status_code != 200:
        return None, None, None
    json_val = r.json()
    if "error" in json_val:  # If route not found, only field is error
        return None, None, None

    return (
        json_val["route_geometry"],
        json_val["route_summary"]["total_time"],
        json_val["route_summary"]["total_distance"],
    )


def get_best_road(lat, lng, radius):
    """Returns the road segment with the largest number of taxis in db
    @param
        lat, lng: current position of client in lat lng
        radius: how far client is willing to walk to hail a taxi
    @return: Location of the best road
    """

    # Locs, tree referred to outside name space
    roads = get_closest_roads(lat, lng, locs, tree, radius)

    max_val = 0
    max_road = None

    for road in roads:
        val = get_count_at_road(road)
        if val > max_val:
            max_val = val
            max_road = road
    return max_road


def get_count_at_road(road):
    """
    @param road: roadID from Location model.
    @return sum of taxi counts at roadID for all time.
    """
    if road == None:
        return 0
    records = road.locationrecord_set.all()
    return sum(map(lambda rec: rec.count, records))


def get_closest_roads(lat, lng, locs, tree, radius):
    """
    @param:
        lat, lng: position of client
        radius: how far client is willing to walk to hail a taxi
    @return: list of closest road segments to the coordinates using kdtree
    """
    road_indexes = tree.query_ball_point((lat, lng), radius / M_PER_LAT)
    return [locs[idx] for idx in road_indexes]


def serialize_coordinates(coordinates):
    """Helper function to serialize list to output as needed in JsonResponse.
    @return serialized list of coordinates.
    """
    return [[float(c.lat), float(c.lng)] for c in coordinates]

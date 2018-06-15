import datetime
import pytz
import math
import json
import requests

from .convert import ConvertHeatmap
from .download import start_download
from .models import Timestamp, Coordinate, Location, LocationRecord
from django.shortcuts import render
from django.conf import settings
from scipy.sparse import coo_matrix
from scipy.spatial import KDTree


# Set up KDTree
import sys

sys.setrecursionlimit(30000)
locs = None
tree = None
try:
    locs = [loc for loc in Location.objects.all()]
    locs = list(filter(lambda x: x.lat != 0, locs))
    if len(locs) > 0:  # Tests initialize kdtree with no values
        tree = KDTree(
            list(map(lambda x: (float(x.lat), float(x.lng)), locs)), leafsize=3000
        )
except Exception as e:
    print(str(e))


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
    """@return coords, average_dist away of cars within 500m radius, num cars within 500m radius"""
    pos = request.GET.get("pos")
    pos = json.loads(pos)
    distFunc = lambda x: math.pow(
        math.pow(110570 * (float(x.lat) - pos["lat"]), 2)
        + math.pow(111320 * (float(x.lng) - pos["lng"]), 2),
        0.5,
    )

    # Approximating lat/lng
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

    best_road = get_best_road(pos["lat"], pos["lng"])
    lat = None
    lng = None
    path_geom = None
    if best_road != None:
        lat = float(best_road.lat)
        lng = float(best_road.lng)
        path_geom = get_path_geom(pos["lat"], pos["lng"], lat, lng)

    return result, total_dist, num, best_road.road_name, lat, lng, path_geom


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


def get_path_geom(start_lat, start_lng, end_lat, end_lng):
    url = "https://developers.onemap.sg/privateapi/routingsvc/route"
    params = {
        "start": "{},{}".format(start_lat, start_lng),
        "end": "{},{}".format(end_lat, end_lng),
        "routeType": "walk",
        "token": settings.ONEMAP_SECRET_KEY,
    }
    r = requests.get(url, params=params)
    if r.status_code != 200:
        return None
    json_val = r.json()
    if "error" in json_val:  # If route not found, only field is error
        return None
    return json_val["route_geometry"]


def get_best_road(lat, lng):
    """Returns the road segment with the largest number of taxis in db
    @param: current position of client in lat lng
    @return: Location of the best road
    """

    roads = get_closest_roads(lat, lng)

    max_val = 0
    max_road = None

    for road in roads:
        val = get_count_at_road(road)
        if val > max_val:
            max_val = val
            max_road = road
    return max_road


def get_count_at_road(road):
    if road == None:
        return 0
    records = road.locationrecord_set.all()
    return sum(map(lambda rec: rec.count, records))


def get_closest_roads(lat, lng):
    """Retrieves the closest road segments to the coordinates using kdtree
    Approximately 500m
    @param: position of client
    @return: list of Locations"""

    road_indexes = tree.query_ball_point((lat, lng), 500 / 110570)
    return [locs[idx] for idx in road_indexes]


def serialize_coordinates(coordinates):
    """Helper function to serialize list to output as needed in JsonResponse.
    @return serialized list of coordinates.
    """
    return [[float(c.lat), float(c.lng)] for c in coordinates]

import datetime

from background_task.models import Task
from daemons.convert import ConvertHeatmap
from daemons.models import Coordinate, Timestamp
from daemons.views import (
    get_coordinates_time,
    get_coordinates_location,
    serialize_coordinates,
    get_best_road,
)
from django.shortcuts import render
from django.utils import timezone
from django.conf import settings
from django.http import JsonResponse
from scipy.sparse import coo_matrix
from scipy.ndimage.morphology import grey_dilation
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
    # coordinates = Timestamp.objects.latest("date_time").coordinate_set.all()
    # hs = HeatmapSlider(serialize_coordinates(coordinates))
    # try:
    #     hs.show()
    # except:
    #     pass
    heattiles, timestamp = get_heatmap_time(request)
    return JsonResponse({"heattiles": heattiles, "timestamp": timestamp.date_time})


def gen_time_js(request):
    """Return Json of serialized list of coordinates according to time."""
    return JsonResponse(
        {"coordinates": serialize_coordinates(get_coordinates_time(request))}
    )


def gen_loc_js(request):
    """Return Json of serialized list of coordinates, average distance away, and number of taxis according to the location"""
    coords, total_dist, number, best_road, lat, lng, path_geom = get_coordinates_location(
        request
    )
    road_id = get_best_road(coords)

    return JsonResponse(
        {
            "coordinates": serialize_coordinates(coords),
            "total_dist": total_dist,
            "number": number,
            "best_road": best_road,
            "best_road_coords": {"lat": lat, "lng": lng},
            "path_geom": path_geom,
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
    @return
        list of heattiles, each with intensity, x-coord, and y-coord.
        timestamp.
    """
    minutes = request.GET.get("minutes")
    sigma = request.GET.get("sigma")
    if minutes == None:
        minutes = 0
    if sigma == None:
        sigma = 1
    else:
        sigma = int(sigma)  # TODO typecast

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
    if times:

        # If many times, Select most recent time.
        time = times[0]

        # TODO is there another way to do this with less conversions?
        coo = ConvertHeatmap.retrieve_heatmap(time)
        heatmap = coo.toarray()
        heatmap = grey_dilation(heatmap, size=(sigma, sigma))
        coo = coo_matrix(heatmap.astype(int))
        return list(zip(coo.data.tolist(), coo.row.tolist(), coo.col.tolist())), time
    else:
        # TODO return value does not fit specification.
        return []


def serialize_coordinates(coordinates):
    """Helper function to serialize list to output as needed in JsonResponse.
    @return serialized list of coordinates.
    """
    return [[float(c.lat), float(c.long)] for c in coordinates]

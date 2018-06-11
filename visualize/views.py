import datetime
import pytz

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
    # TODO remove.
    # This code is to show developers heatmap in GUI, and change variables on the fly.
    # The code is here to access database while Apps are registered.

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


def slider_js(request):
    """Render Javascript file with list of coordinates in context."""
    return render(
        request, "visualize/slider.js", {"SLIDE_EVENT": settings.SLIDE_EVENT}
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
    if times:

        # If many times, Select most recent time.
        time = times[0]

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
        # TODO return value does not fit specification.
        return []


def get_chart_data_js(request):
    timezone.activate(pytz.timezone(settings.TIME_ZONE))
    date_time_end = Timestamp.objects.latest("date_time").date_time
    # TODO: Uncomment below. Currently this way cause not enough data
    # date_time_end = timezone.localtime(date_time_end)
    # date_time_end = date_time_end.replace(hour=0, minute=0, second=0)
    date_time_end = date_time_end.replace(second=0)  # remove this in future.
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

    day_stats = [timestamp.taxi_count for timestamp in timestamps]
    return JsonResponse({"day_stats": day_stats})


def serialize_coordinates(coordinates):
    """Helper function to serialize list to output as needed in JsonResponse.
    @return serialized list of coordinates.
    """
    return [[float(c.lat), float(c.long)] for c in coordinates]

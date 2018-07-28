import datetime
import pytz

from background_task.models import Task
from daemons.models import Coordinate, Timestamp, Location
from daemons.views import (
    get_coordinates_time,
    get_coordinates_location,
    get_heatmap_time,
    serialize_coordinates,
    get_best_road,
    get_chart_data,
)
from django.shortcuts import render
from django.utils import timezone
from django.conf import settings
from django.http import JsonResponse
from visualize.heatmap_slider import HeatmapSlider
from daemons.farecalculator import calculateCost


def index(request):
    """View function for home page of site."""
    context = {
        "GOOGLEMAPS_SECRET_KEY": settings.GOOGLEMAPS_SECRET_KEY,
        "error_message": "Location is not accurate.",
    }
    index = (
        "mobile/index.html" if request.user_agent.is_mobile else "visualize/index.html"
    )

    # Else: render with normal context.
    return render(request, index, context)


def gen_heatmap_js(request):
    """Return Json of intensity, coords, and timestamp of heat tile."""
    heattiles, timestamp = get_heatmap_time(request)
    if timestamp == None:
        return JsonResponse({"heattiles": heattiles, "timestamp": None})
    return JsonResponse({"heattiles": heattiles, "timestamp": timestamp.date_time})


def gen_time_js(request):
    """Return Json of serialized list of coordinates according to time."""
    return JsonResponse(
        {"coordinates": serialize_coordinates(get_coordinates_time(request))}
    )


def gen_loc_js(request):
    """Return Json of serialized list of coordinates, average distance away, and number of taxis according to the location"""
    coords, total_dist, number, best_road_name, lat, lng, path_geom, path_instructions, path_time, path_dist = get_coordinates_location(
        request
    )

    return JsonResponse(
        {
            "coordinates": serialize_coordinates(coords),
            "total_dist": total_dist,
            "number": number,
            "best_road": best_road_name,
            "best_road_coords": {"lat": lat, "lng": lng},
            "path_geom": path_geom,
            "path_instructions": path_instructions,
            "path_time": path_time,
            "path_dist": path_dist,
        }
    )


if settings.VISUALIZE_LOCATIONS:

    def map_js(request):
        """Render Javascript file with coordinates of Locations."""
        return render(
            request,
            "visualize/map.js",
            {
                "coordinates": Location.objects.exclude(
                    lat=1.352083, lng=103.819836
                ).all()
            },
        )


else:

    def map_js(request):
        """Render Javascript file with list of coordinates in context."""
        return render(
            request,
            "visualize/map.js",
            {
                "coordinates": get_coordinates_time(request),
                "mobile": request.user_agent.is_mobile,
            },
        )


def slider_js(request):
    """Render Javascript file with list of coordinates in context."""
    return render(request, "visualize/slider.js", {"SLIDE_EVENT": settings.SLIDE_EVENT})


def chart_js(request):
    """Render Javascript file."""
    return render(request, "visualize/chart.js")


def ui_base_js(request, app):
    """Render Javascript file."""
    context = {"GOOGLEMAPS_SECRET_KEY": settings.GOOGLEMAPS_SECRET_KEY}
    return render(request, app + "/ui.js", context)


def ui_mobile_js(request):
    return ui_base_js(request, "mobile")


def ui_js(request):
    return ui_base_js(request, "visualize")


def stats_js(request):
    """Render Javascript file."""
    return render(
        request, "visualize/stats.js", {"mobile": request.user_agent.is_mobile}
    )


def gen_chart_js(request):
    day_stats, chart_title = get_chart_data(request)
    return JsonResponse({"day_stats": day_stats, "chart_title": chart_title})


def get_cost_data_js(request):
    cost = calculateCost(request.GET.get("distance"), request.GET.get("time"))
    return JsonResponse({"cost": cost})

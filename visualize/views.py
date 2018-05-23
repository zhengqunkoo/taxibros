from django.shortcuts import render
from daemons.models import Coordinate, Timestamp
from django.utils import timezone
import datetime
import os
import pytz
from django.http import JsonResponse

def index(request):
    """View function for home page of site."""
    return render(
        request,
        'visualize/index.html',
        {"GOOGLEMAPS_SECRET_KEY": os.getenv("GOOGLEMAPS_SECRET_KEY")}
    )

def get_coordinates(request):
    """Filter range one minute long, ensures at least one date_time returned.
    If two date_times returned, select most recent one.
    @param request: HTTP GET request containing other variables.
        minutes:
            predict taxi locations at this amount of time into the future.
            default: 0.
    @return list of coordinates.
    """
    minutes = request.GET.get('minutes')
    if minutes == None:
        minutes = 0
    now = datetime.datetime.now(pytz.utc)
    start_window = datetime.timedelta(minutes=int(minutes)+1)
    end_window = datetime.timedelta(minutes=int(minutes))
    times = Timestamp.objects.filter(
        date_time__range=(
            now - start_window,
            now - end_window
        ),
    )
    # If no times, return empty list.
    coordinates = []
    if times:
        # If many times, Select most recent time.
        time = times[0]
        print(start_window, end_window)
        print(time)
        coordinates = time.coordinate_set.all()
    return coordinates

def get_coordinates_serial(request):
    """Need serialize list to output as JsonResponse.
    @return serialized list of coordinates.
    """
    return [[c.lat, c.long] for c in get_coordinates(request)]

def gen_js(request):
    """Return Json of serialized list of coordinates."""
    return JsonResponse({'coordinates': get_coordinates_serial(request)})

def maps_js(request):
    """Render Javascript file with list of coordinates in context."""
    return render(
        request,
        'visualize/maps.js',
        {'coordinates': get_coordinates(request)}
    )

from django.shortcuts import render
from daemons.models import Coordinate, Timestamp
from django.utils import timezone
from itertools import chain
import datetime

def index(request):
    """View function for home page of site."""

    return render(
        request,
        'visualize/index.html'
    )
def genjs(request):
    # Render the js template index.html with the data in the context variable.
    # Filters with a 5 minute timespan
    times = Timestamp.objects.filter(date_and_time__range = [timezone.now() - datetime.timedelta(minutes=5), timezone.now()])

    coordinates = []
    for time in times:
        coordinates = chain(time.coordinate_set.all(), coordinates)
    context = {'coordinates':coordinates}

    return render(
            request,
            'visualize/maps.js',
            context
            )

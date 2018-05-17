from django.shortcuts import render
from logging import getLogger

from .models import Timestamp, Coordinate
from .download import start_download


def index(request):
    """View function for home page of site."""

    # Count objects.
    num_timestamps = Timestamp.objects.count()
    num_coordinates = Coordinate.objects.count()

    logger = getLogger(__name__)
    logger.debug('daemons.views.index')
    start_download(repeat=60, repeat_until=None)
    
    # Render the HTML template index.html with the data in the context variable.
    return render(
        request,
        'index.html',
        context={
            'num_timestamps':num_timestamps,
            'num_coordinates':num_coordinates,
        },
    )

from django.shortcuts import render
from daemons.models import Coordinate
def index(request):
    """View function for home page of site."""

    return render(
        request,
        'visualize/index.html'
    )
def genjs(request):
    # Render the js template index.html with the data in the context variable.
    coordinates = Coordinate.objects.all()
    context = {'coordinates':coordinates}

    return render(
            request,
            'visualize/maps.js',
            context
            )

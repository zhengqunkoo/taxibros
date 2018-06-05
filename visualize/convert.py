import datetime
import numpy as np

from daemons.models import Timestamp
from daemons.views import serialize_coordinates
from django.conf import settings
from django.utils import dateparse, timezone
from .models import Heatmap


class ConvertHeatmap:
    """Converts coordinates into heatmap.
    Heatmap is sparse matrix of intensities (mostly zeros).
    """

    def __init__(self, bins=50):
        """
        @param bins: number of bins along each of the x-, y-axes. Default 50.
            Total number of bins is (@param bins**2).
        """
        self._bins = bins

        # Range of date_time to filter timestamps.
        self._date_time_start = dateparse.parse_datetime(settings.DATE_TIME_START)
        self._date_time_end = timezone.now()

    def store(self):
        """Stores heatmaps within time range."""
        times = Timestamp.objects.filter(
            date_time__range=(self._date_time_start, self._date_time_end)
        )
        for time in times:
            print("Store {}".format(time))

            # Store as heat tile.
            for index, intensity in np.ndenumerate(self.convert(time)):
                Heatmap(
                    intensity=intensity, x=index[0], y=index[1], timestamp=time
                ).save()

    def convert(self, time):
        """Convert coordinates into heatmap.
        @param time: daemons.models.Timestamp object to be stored.
        @return heatmap: numpy array of intensities.
        """
        coordinates = time.coordinate_set.all()
        y, x = zip(*serialize_coordinates(coordinates))
        heatmap, _, _ = np.histogram2d(x, y, bins=self._bins)
        return heatmap


if __name__ == "__main__":
    import os
    import django
    from taxibros.wsgi import application

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "taxibros.settings.local_settings")
    django.setup()
    ch = ConvertHeatmap()
    ch.store()

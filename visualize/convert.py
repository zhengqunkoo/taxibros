import datetime
import numpy as np
from scipy.sparse import coo_matrix

from daemons.models import Timestamp
from daemons.views import serialize_coordinates
from django.conf import settings
from django.utils import dateparse, timezone
from .models import Heatmap


class ConvertHeatmap:
    """Converts coordinates into heatmap.
    Heatmap is sparse matrix of intensities (mostly zeros).
    """

    def __init__(self, bins=500):
        """
        @param bins: number of bins along each of the x-, y-axes. Default 50.
            Total number of bins is (@param bins**2).
        """
        self._bins = bins

        # Range of date_time to filter timestamps.
        self._date_time_start = dateparse.parse_datetime(settings.DATE_TIME_START)
        self._date_time_end = timezone.now()

    def store(self):
        """Stores heatmaps within time range.
        Store as sparse matrix, do not store zeros.
        """
        times = Timestamp.objects.filter(
            date_time__range=(self._date_time_start, self._date_time_end)
        )
        for time in times:
            print("Convert {}".format(time))

            # Store as heat tile.
            coo = self.convert(time)
            for x, y, v in zip(coo.row, coo.col, coo.data):
                Heatmap(intensity=v, x=x, y=y, timestamp=time).save()

    def convert(self, time):
        """Convert coordinates of a timestamp into heatmap.
        Note:
            Database could return empty coordinate set.
            Then, return heatmap with all zeros.
        @param time: daemons.models.Timestamp object to be stored.
        @return heatmap: scipy sparse integer coordinate matrix of intensities.
        """
        coordinates = time.coordinate_set.all()
        serialized = serialize_coordinates(coordinates)
        if serialized:
            lat, long = zip(*serialized)
        else:
            lat, long = [], []
        heatmap, _, _ = np.histogram2d(lat, long, bins=self._bins)
        return coo_matrix(heatmap.astype(int))

if __name__ == "__main__":
    import os
    import django
    from taxibros.wsgi import application

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "taxibros.settings.local_settings")
    django.setup()
    ch = ConvertHeatmap()
    ch.store()

import datetime
import numpy as np
from scipy.sparse import coo_matrix

from .models import Timestamp, Heatmap
from django.conf import settings
from django.utils import dateparse, timezone


class ConvertHeatmap:
    """Converts coordinates into heatmap.
    Heatmap is sparse matrix of intensities (mostly zeros).
    """

    def __init__(self, xbins=890, ybins=531):
        """
        @param xbins, ybins: number of bins along each of the x-, y-axes.
            Default:
                Width and height of Singapore in terms of lng, lat.
                width, height: 0.445, 0.2655 (lng, lat).
                xbins, ybins: 4450, 2655 is 4 decimal place accuracy.
                See https://en.wikipedia.org/wiki/Decimal_degrees.

                Excludes some islands (assume no taxis in islands).
                Lower left: 1.205, 103.605 (lat, lng).
                Upper right: 1.4705, 104.05 (lat, lng).
            Total number of bins in heatmap is (@param bins**2).
        """
        self._xbins = xbins
        self._ybins = ybins

    def store_heatmap(self, timestamp, coordinates):
        """Stores heatmaps within time range.
        Store as sparse matrix, do not store zeros.
        @param timestamp: Timestamp object of LTA date_time that JSON was updated.
        @param coordinates: list of coordinates to be stored.
        """
        print("Convert {}".format(timestamp))

        # Store as heat tile.
        coo, xedges, yedges = self.convert(coordinates)
        for v, x, y in zip(coo.data, coo.row, coo.col):
            Heatmap(
                intensity=v,
                x=x,
                y=y,
                lat=xedges[x],
                long=yedges[y],
                timestamp=timestamp,
            ).save()

    @classmethod
    def retrieve_heatmap(cls, timestamp):
        """
        @param timestamp: Timestamp object of LTA date_time that JSON was updated.
        @return
            coo_matrix of heatmap of the timestamp.
            xedges, yedges: list of coordinate values for each heattile.
        """
        heatmap = timestamp.heatmap_set.all()
        xedges, yedges = zip(*serialize_coordinates(heatmap))
        return (
            coo_matrix(
                (
                    [heattile.intensity for heattile in heatmap],
                    (
                        [heattile.x for heattile in heatmap],
                        [heattile.y for heattile in heatmap],
                    ),
                )
            ),
            xedges,
            yedges,
        )

    def convert(self, coordinates):
        """Convert coordinates of a timestamp into heatmap.
        Note:
            Database could return empty coordinate set.
            Then, return heatmap with all zeros.
        @param coordinates: list of coordinates.
        @return
            heatmap: scipy sparse integer coordinate matrix of intensities.
            xedges, yedges: list of coordinate values for each heattile.
        """
        if coordinates:
            lat, long = zip(*coordinates)
        else:
            lat, long = [], []
        heatmap, xedges, yedges = np.histogram2d(
            long, lat, bins=(self._xbins, self._ybins)
        )
        return coo_matrix(heatmap.astype(int)), xedges, yedges


# TODO duplicate code from daemons.views
def serialize_coordinates(coordinates):
    """Helper function to serialize list to output as needed in JsonResponse.
    @return serialized list of coordinates.
    """
    return [[float(c.lat), float(c.long)] for c in coordinates]

import datetime
import numpy as np
import requests
from scipy.sparse import coo_matrix

from .models import Heatmap, Heattile, Location, LocationRecord
from django.conf import settings
from django.utils import dateparse, timezone
from django.db import OperationalError
from scipy.spatial import KDTree


# Approximating lat/lng
# http://www.longitudestore.com/how-big-is-one-gps-degree.html
M_PER_LAT = 110570
M_PER_LONG = 111320

# Set up KDTree once on server start.
import sys

sys.setrecursionlimit(30000)
try:
    locs = [loc for loc in Location.objects.all()]
    locs = list(filter(lambda x: x.lat != 0, locs))
    if len(locs) > 0:  # Tests initialize kdtree with no values
        tree = KDTree(
            list(map(lambda x: (float(x.lat), float(x.lng)), locs)), leafsize=3000
        )
        print("Successfully populated KDTree.")
    else:
        tree = KDTree([[], []])
        print("Initialized empty KDTree, due to locs empty.")
except OperationalError as e:
    print("Error accessing daemons_location, see: {}.".format(e))
    locs = []
    tree = KDTree([[], []])
else:
    print("Successfully populated locs and tree.")


class ConvertHeatmap:
    """Converts coordinates into heatmap.
    Heatmap is sparse matrix of intensities (mostly zeros).
    """

    def __init__(self, xbins=531, ybins=890):
        """
        @param xbins, ybins: number of bins along each of the x-, y-axes.
            Default:
                Width and height of Singapore in terms of lng, lat.
                width, height: 0.445, 0.2655 (lng, lat).
                xbins, ybins: 531, 890 is 3.5 decimal place accuracy.
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
        print("ConvertHeatmap {}".format(timestamp))

        # Store as heat tile.
        coo = self.convert(coordinates)
        coo, left, right, bottom, top = self.convert(coordinates)
        heatmap = Heatmap(
            left=left,
            right=right,
            bottom=bottom,
            top=top,
            xbins=self._xbins,
            ybins=self._ybins,
            timestamp=timestamp,
        )
        heatmap.save()
        for v, x, y in zip(coo.data, coo.row, coo.col):
            Heattile(intensity=v, x=x, y=y, heatmap=heatmap).save()

    @classmethod
    def retrieve_heatmap(cls, time):
        """
        @param timestamp: Timestamp object of LTA date_time that JSON was updated.
        @return
            coo_matrix of heatmap of the timestamp.
            left, right, bottom, top, xbins, ybins: Heatmap object attributes.
        """
        heatmap = time.heatmap
        heattile = heatmap.heattile_set.all()
        intensities, xs, ys = zip(*[[h.intensity, h.x, h.y] for h in heattile])
        return (
            coo_matrix((intensities, (xs, ys))),
            heatmap.left,
            heatmap.right,
            heatmap.bottom,
            heatmap.top,
            heatmap.xbins,
            heatmap.ybins,
        )

    def convert(self, coordinates):
        """Convert coordinates of a timestamp into heatmap.
        Note:
            Database could return empty coordinate set.
            Then, return heatmap with all zeros.
        @param coordinates: list of coordinates.
        @return
            heatmap: scipy sparse integer coordinate matrix of intensities.
            left, right, bottom, top: extent of data.
        """
        if coordinates:
            lats, lngs = zip(*coordinates)
        else:
            lats, lngs = [], []
        heatmap, xedges, yedges = np.histogram2d(
            lngs, lats, bins=(self._xbins, self._ybins)
        )
        return (
            coo_matrix(heatmap.astype(int)),
            xedges[0],
            xedges[-1],
            yedges[0],
            yedges[-1],
        )


class ConvertRoad:
    def __init__(self):
        pass

    @classmethod
    def process_closest_roads(cls, coordinates, timestamp):
        """Processes the coordinates by tabulating counts for their respective road segments
        """
        print("ConvertRoad {}".format(timestamp))
        print("Number of grid points (sanity check): {}.".format(len(coordinates)))

        try:
            # corresponding points of kdtree are returned to passed in coordinates
            # distances: distance of coordinate from closest coordinate in kdtree
            # indexes: index of closest coordinate in tree.data
            # These two arrays are sorted by distance
            distances, indexes = tree.query(coordinates)
            # Assumption: data is an array of
            data = tree.data
            # threshold if coordinate is too far from any closest road dont store
            threshold = 20 / M_PER_LAT
            vals = {}
            for i in range(len(indexes)):
                if distances[i] > threshold:
                    continue
                if vals[data[i]] not in vals:
                    vals[data[i]] = 1
                else:
                    vals[data[i]] += 1
            cls.store_road_data(vals, timestamp)

        except Exception as e:
            print(str(e))

    @classmethod
    def store_road_data(cls, vals, timestamp):
        """Stores a dictionary of road ids and count into a db
        """
        for coord, count in vals.items():
            try:
                location = find_corresponding_location(coord)
                LocationRecord(
                    count=count, location=location, timestamp=timestamp
                ).save()
            except Exception as e:
                print(str(e))
                print("Corresponding location for coordinate not found in db:")
                print(str(coord))

    @classmethod
    def find_corresponding_location(coordinate):
        """Finds corresponding location from coordinate
        If not found, django model manager get will raise does not exist error
        If multiple objects found, django model will raise multiple objects returned error"""
        lat = coordinate[0]
        lng = coordinate[1]
        location = Location.objects.get(lat=lat, lng=lng)
        return location

    @classmethod
    def get_road_info_from_id(cls, roadID, tries=4):
        if tries == 0:
            raise Exception("Cannot get location")
        url = (
            "https://maps.googleapis.com/maps/api/place/details/json?placeid="
            + roadID
            + "&key="
            + settings.GOOGLEMAPS_SECRET_KEY
        )
        r = requests.get(url)
        if r.status_code != 200:
            time.sleep(1)
            return get_road_info_from_id(roadID, tries=tries - 1)
        json_val = r.json()
        if "error_message" in json_val:
            raise Exception(json_val["error_message"])
        if json_val["status"] == "NOT_FOUND":
            raise Exception("RoadID not available")
        # Sometimes, road_name is just Singapore
        road_name = json_val["result"]["name"]
        if road_name == "Singapore":
            road_name = "Unnamed Road"

        coordinates = json_val["result"]["geometry"]["location"]
        lat = coordinates["lat"]
        lng = coordinates["lng"]

        return lat, lng, road_name

    @classmethod
    def process_location_coordinates(cls, road_id):
        """Store @param road_id as a Location model along with other info."""
        location, created = Location.objects.get_or_create(pk=road_id)
        lat, lng, road_name = cls.get_road_info_from_id(road_id)
        Location(roadID=road_id, road_name=road_name, lat=lat, lng=lng).save()


def process_location_coordinates():
    """Auxiliary task to run after sufficient downloads of information to update locaiton info
    with lat lng and road_name"""
    locations = Location.objects.filter(lat=0)

    print("Total to process: " + str(len(locations)))
    count = 1
    for loc in locations:
        print(str(count) + ": Processing " + loc.roadID)
        count += 1
        try:
            lat, lng, road_name = ConvertRoad.get_road_info_from_id(loc.roadID)
            loc.lat = lat
            loc.lng = lng
            loc.road_name = road_name
            loc.save()
        except Exception as e:
            loc.delete()
            print(str(e))

import datetime
import numpy as np
import requests
from scipy.sparse import coo_matrix

from .models import Heatmap, Heattile, Location, LocationRecord
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
        try:
            # Breaks coordinates into smaller chunks due to error 413
            coord_chunks = [
                coordinates[x : x + 100] for x in range(0, len(coordinates), 100)
            ]
            vals = {}
            for coord_chunk in coord_chunks:
                cls.add_list_to_dict(cls.get_closest_roads(coord_chunk), vals)
            cls.store_road_data(vals, timestamp)

        except Exception as e:
            print(str(e))

    @classmethod
    def get_closest_roads(cls, coordinates):
        """Retrieves the closest road segments to the coordinates
        @param: coordinates of the taxis
        @return: list of same size as coordinates containing road segment or None if none is found"""
        coords_params = "|".join(
            [
                str(coordinate[1]) + "," + str(coordinate[0])
                for coordinate in coordinates
            ]
        )
        url = (
            "https://roads.googleapis.com/v1/nearestRoads?points="
            + coords_params
            + "&key="
            + settings.GOOGLEMAPS_SECRET_KEY
        )
        json_val = cls.get_json(cls, url)
        result = [None] * len(coordinates)
        for point in json_val["snappedPoints"]:
            index = point["originalIndex"]
            if (result[index] != None and point["placeId"] > result[index]) or result[
                index
            ] == None:
                result[index] = point["placeId"]
        return result

    @classmethod
    def add_list_to_dict(cls, road_id_list, vals):
        """Stores a road_id_list into a dictionary
        """
        for id in road_id_list:
            if id == None:
                continue
            if id in vals:
                vals[id] += 1
            else:
                vals[id] = 1

    @classmethod
    def store_road_data(cls, vals, timestamp):
        """Stores a dictionary of road ids and count into a db
        """
        for id, count in vals.items():
            location, created = Location.objects.get_or_create(pk=id)
            LocationRecord(count=count, location=location, timestamp=timestamp).save()


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
            lat, lng, road_name = get_road_info_from_id(loc.roadID)
            loc.lat = lat
            loc.lng = lng
            loc.road_name = road_name
            loc.save()
        except Exception as e:
            loc.delete()
            print(str(e))


def get_road_info_from_id(roadID, tries=4):
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
    if r.json()["status"] == "NOT_FOUND":
        raise Exception("RoadID not available")
    # Sometimes, road_name is just Singapore
    road_name = json_val["result"]["name"]
    if road_name == "Singapore":
        road_name = "Unnamed Road"

    coordinates = json_val["result"]["geometry"]["location"]
    lat = coordinates["lat"]
    lng = coordinates["lng"]

    return lat, lng, road_name

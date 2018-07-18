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

if settings.INITIALIZE_KDTREE:

    # Set up KDTree once on server start.
    import sys

    sys.setrecursionlimit(30000)
    try:
        locs = list(filter(lambda x: x.lat != 0, Location.objects.all()))
        locs = list(set(map(lambda x: (float(x.lat), float(x.lng)), locs)))
        if len(locs) > 0:  # Tests initialize kdtree with no values
            tree = KDTree(
                locs, leafsize=3000
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


class ConvertLocation:
    def __init__(self):
        pass

    @classmethod
    def get_json_nearest_roads(cls, url):
        """Generic method to download nearest roads
        @param url: URL to download from.
        @return JSON.
        """
        response = requests.get(url)
        return response.json()

    @classmethod
    def get_json_road_info(cls, url, tries=4):
        """Generic method to download road info
        @param url: URL to download from.
        @return JSON.
        """
        if tries == 0:
            raise Exception("Cannot get location")
        response = requests.get(url)
        if response.status_code != 200:
            # Retries if status code not 200. Road info is important.
            time.sleep(1)
            return cls.get_json_road_info(url, tries=tries - 1)
        return response.json()

    ##########################
    ##Downloading Locations###
    ##########################
    @classmethod
    def store_locations(cls, coordinates):
        """Entry point to save many @param coordinates as many Locations."""
        print("Number of coordinates (sanity check): {}.".format(len(coordinates)))
        for coord_chunk in cls.get_coord_chunks(coordinates):
            print("Processing coord chunk of length {}.".format(len(coord_chunk)))
            for road_id in cls.get_closest_roads_api(coord_chunk):
                if road_id:  # If not none.
                    print("Processing {}".format(road_id))
                    cls.store_location(road_id)
        print("Processing finished!")

    @classmethod
    def get_coord_chunks(cls, coordinates):
        """
        Breaks coordinates into smaller chunks due to error 413.
        """
        return [coordinates[x : x + 100] for x in range(0, len(coordinates), 100)]

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
    def get_closest_roads_api(cls, coordinates):
        """Retrieves the closest road segments to the coordinates
        Used ONLY during initial downloading of all location coordinates
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

        # Need this call for mock tests.
        json_val = cls.get_json_nearest_roads(url)
        result = [None] * len(coordinates)

        # Ignore case when no points snap to any road.
        if json_val:
            for point in json_val["snappedPoints"]:
                index = point["originalIndex"]
                if (
                    result[index] != None and point["placeId"] > result[index]
                ) or result[index] == None:
                    result[index] = point["placeId"]

        return result

    @classmethod
    def store_location(cls, road_id):
        """Store @param road_id as a Location model along with other info."""
        location, created = Location.objects.get_or_create(pk=road_id)
        if created:
            print("Created    {}".format(road_id))
            cls.store_location_data(road_id)

    @classmethod
    def store_location_data(cls, road_id):
        """Get other info and store @param road_id as Location."""
        try:
            lat, lng, road_name = cls.get_road_info_from_id(road_id)
            print("Got data   {}".format(road_id))
            Location(roadID=road_id, road_name=road_name, lat=lat, lng=lng).save()
        except Exception as e:
            print(str(e))

    @classmethod
    def get_road_info_from_id(cls, roadID):

        url = (
            "https://maps.googleapis.com/maps/api/place/details/json?placeid="
            + roadID
            + "&key="
            + settings.GOOGLEMAPS_SECRET_KEY
        )
        json_val = cls.get_json_road_info(url)

        if "error_message" in json_val:
            raise Exception(json_val["error_message"])
        if json_val["status"] == "NOT_FOUND":
            raise Exception("RoadID not available")
        if json_val["status"] == "INVALID_REQUEST":
            raise Exception("Invalid Request. Check params")
        # Sometimes, road_name is just Singapore
        road_name = json_val["result"]["name"]
        if road_name == "Singapore":
            road_name = "Unnamed Road"

        coordinates = json_val["result"]["geometry"]["location"]
        lat = coordinates["lat"]
        lng = coordinates["lng"]

        return lat, lng, road_name


class ConvertLocationRecords:
    def __init__(self):
        pass

    @classmethod
    def store_location_records(cls, coordinates, timestamp):
        """Processes the coordinates by tabulating counts for their respective road segments
        """
        print("ConvertLocation {}".format(timestamp))
        try:
            vals = cls.get_closest_roads_kdtree(coordinates)
            cls.store_location_record_data(vals, timestamp)
            print("    Success!")

        except Exception as e:
            print(str(e))

    @classmethod
    def get_closest_roads_kdtree(cls, coordinates):
        """Retrieves the closest road segments to the coordinates
        Used ONLY during download of location records
        @param: coordinates of the taxis
        @return: Dictionary of values where keys are coordinates in tuple and value is count"""
        # corresponding points of kdtree are returned to passed in coordinates
        # distances: distance of coordinate from closest coordinate in kdtree
        # indexes: index of closest coordinate in tree.data
        # These two arrays are sorted by distance
        coordinates = list(map(lambda x: (x[1], x[0]), coordinates))
        distances, indexes = tree.query(coordinates)

        # Assumption: data is an array of
        data = tree.data
        # threshold if coordinate is too far from any closest road dont store
        threshold = 300 / M_PER_LAT
        exceed_thresh_count = 0
        vals = {}
        for i in range(len(indexes)):
            key = tuple(data[indexes[i]])
            if distances[i] > threshold:
                exceed_thresh_count += 1
                continue
            if key not in vals:
                vals[key] = 1
            else:
                vals[key] += 1
        print(
            "Percentage of coordinates without coresponding location: {}%".format(
                100 * exceed_thresh_count / len(coordinates)
            )
        )
        return vals

    @classmethod
    def store_location_record_data(cls, vals, timestamp):
        """Stores a dictionary of road ids and count into a db
        """
        for coord, count in vals.items():
            try:
                location = cls.find_corresponding_location(coord)
                LocationRecord(
                    count=count, location=location, timestamp=timestamp
                ).save()
            except Exception as e:
                print("Error in finding coordinate:")
                print("    " + str(e))
                print("    " + str(coord))

    @classmethod
    def find_corresponding_location(cls, coordinate):
        """Finds corresponding location from coordinate
        If not found, django model manager get will raise does not exist error
        If multiple objects found, return one object.
        """
        lat = coordinate[0]
        lng = coordinate[1]
        locations = Location.objects.filter(lat=lat, lng=lng)
        return locations[0]

import abc
from background_task import background
from background_task.models import Task
import datetime
from logging import getLogger
import pytz
import requests
import time

from .convert import ConvertHeatmap
from .models import Timestamp, Coordinate, Location, LocationRecord, Heatmap
from django.utils import dateparse, timezone
from django.conf import settings


class DownloadJson:
    """Download one JSON stream using HTTP GET.
    Assume stream has timestamp (when data was last updated).
    Stores all JSON data, with timestamps, in a database.

    Search for missing timestamps within a date_time range.
    Range is (settings.DATE_TIME_START, now).
    For each missing timestamp, download it.
    """

    def __init__(self, url):
        """@param url: url to download JSON data from."""
        self._url = url
        self._logger = getLogger(__name__)

        # Range of date_time to search missing timestamps.
        self._date_time_start = dateparse.parse_datetime(settings.DATE_TIME_START)
        self._date_time_end = timezone.now()

    @abc.abstractmethod
    def get_time_features(self, json_val):
        """Given a JSON, extract features and time.
        @return date_time: server-side time that JSON was updated.
        @return features: JSON features to be logged or stored.
        """
        ...

    @abc.abstractmethod
    def get_coordinates(self, json_val):
        """Given a JSON, extract coordinates.
        @return coordinates: tuple or list of coordinates.
        """
        ...

    @abc.abstractmethod
    def get_properties(self, json_val):
        """Given a JSON, extract properties.
        @return taxi_count, status of API.
        """
        ...

    def download(self, url=None):
        """Generic method to download JSON streams.
        @param url: URL to download from. Default: None.
        @return date_time: LTA date_time that JSON was updated.
        """
        json_val = self.get_json(url)

        # Log errors and exit from function if error.
        # Assume 'code' or 'message' in JSON means error.
        contains_code = "code" in json_val
        contains_message = "message" in json_val
        if contains_code or contains_message:
            error_array = []
            if contains_code:
                error_array.append(json_val["code"])
            if contains_message:
                error_array.append(json_val["message"])
            self.log(*error_array)
            return

        date_time, features = self.get_time_features(json_val)
        taxi_count, status = self.get_properties(features)
        self.log(date_time, taxi_count, status)
        coordinates = self.get_coordinates(features)
        self.store_timestamp_coordinates(date_time, taxi_count, coordinates)
        return date_time

    def get_json(self, url=None):
        """Generic method to download JSON streams.
        @param url: URL to download from. Default: self._url.
        @return JSON.
        """
        if url == None:
            url = self._url
        response = requests.get(url)
        return response.json()

    def store_timestamp_coordinates(self, date_time, taxi_count, coordinates):
        """If date_time is not unique, do not do anything.
        Stores each coordinate with the same unique date_time.

        @param date_time: LTA date_time that JSON was updated.
        @param taxi_count: Number of taxis in timestamp.
        @param coordinates: list of coordinates to be stored.
        @return
            created: True if unique date_time, False if duplicate date_time.
            timestamp: Timestamp object of LTA date_time that JSON was updated.
            coordinates: list of coordinates to be stored.
        """
        timestamp, created = Timestamp.objects.get_or_create(
            date_time=date_time, taxi_count=taxi_count
        )
        if created:
            # Dont uncomment unless you know what you are doing
            self.process_closest_roads(coordinates, timestamp)

            # If created timestamp, store coordinates.
            print("Store {}".format(date_time))
            for coordinate in coordinates:
                Coordinate(
                    lat=coordinate[1], long=coordinate[0], timestamp=timestamp
                ).save()
        return created, timestamp, coordinates

    def download_missing_timestamps(self):
        """Get current timestamps in database. Identify missing timestamps.
        Timestamps are more or less 60 seconds apart.
        But sometimes they are 90 seconds apart, subsequently 30 seconds apart.
        @return missing: sorted list of missing timestamps.
        """
        times = Timestamp.objects.filter(
            date_time__range=(self._date_time_start, self._date_time_end)
        )

        # Convert to local timezone.
        # Get sorted filtered timestamps, between start and end.
        timezone.activate(pytz.timezone(settings.TIME_ZONE))
        times = sorted(
            [self._date_time_start, self._date_time_end]
            + [timezone.localtime(x.date_time) for x in times]
        )

        # If current and next timestamps more than missing_seconds apart,
        # then there could be a missing timestamp before (current + missing_seconds).
        # If not, then there must be a missing timestamp before (current + missing_seconds_long).
        # If not, raise exception.
        missing_seconds = 65
        missing_seconds_long = 95
        missing = []
        for i in range(len(times) - 1):
            cur, next = times[i], times[i + 1]

            # Download all contiguous missing timestamps.
            while (next - cur).seconds > missing_seconds:
                missing = self.download_missing_timestamp(cur, missing_seconds)

                # Try longer missing seconds.
                if cur == missing:
                    missing = self.download_missing_timestamp(cur, missing_seconds_long)
                    if cur == missing:
                        raise Exception(
                            "Gap between adjacent timestamps greater than {} seconds.".format(
                                missing_seconds_long
                            )
                        )
                cur = missing

    def download_missing_timestamp(self, cur, seconds):
        """
        @param cur: current timestamp.
        @param seconds: time after @param cur to query the API with.
        @return datetime object of LTA timestamp.
        """
        missing = cur + datetime.timedelta(seconds=seconds)
        missing = missing.strftime("%Y-%m-%dT%H:%M:%S")
        print("Check {}".format(missing))
        date_time = self.download("{}?date_time={}".format(self._url, missing))
        return dateparse.parse_datetime(date_time)

    def download_timestamps(self):
        """Make timestamps in database continuous, in terms of minutes.
        Also, download with latest timestamp.
        """
        self.download_missing_timestamps()
        print("Check latest")
        self.download()
        print("Stored all missing timestamps!")

    def log(self, *args):
        """Logs with space-separated list of strings.
        @param args: list of values that can be converted into strings.
        """
        self._logger.debug(" ".join(map(str, args)))

    def process_closest_roads(self, coordinates, timestamp):
        """Processes the coordinates by tabulating counts for their respective road segments
        """
        try:
            # Breaks coordinates into smaller chunks due to error 413
            coord_chunks = [
                coordinates[x : x + 100] for x in range(0, len(coordinates), 100)
            ]
            vals = {}
            for coord_chunk in coord_chunks:
                self.add_list_to_dict(self.get_closest_roads(coord_chunk), vals)
            self.store_road_data(vals, timestamp)

        except Exception as e:
            print(str(e))

    def get_closest_roads(self, coordinates):
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
        json_val = self.get_json(url)
        result = [None] * len(coordinates)
        for point in json_val["snappedPoints"]:
            index = point["originalIndex"]
            if (result[index] != None and point["placeId"] > result[index]) or result[
                index
            ] == None:
                result[index] = point["placeId"]
        return result

    def add_list_to_dict(self, road_id_list, vals):
        """Stores a road_id_list into a dictionary
        """
        for id in road_id_list:
            if id == None:
                continue
            if id in vals:
                vals[id] += 1
            else:
                vals[id] = 1

    def store_road_data(self, vals, timestamp):
        """Stores a dictionary of road ids and count into a db
        """
        for id, count in vals.items():
            location, created = Location.objects.get_or_create(pk=id)
            LocationRecord(count=count, location=location, timestamp=timestamp).save()


def process_location_coordinates():
    locations = Location.objects.filter(lat=0)

    print("Total to process: " + str(len(locations)))
    count = 1
    for loc in locations:
        print(str(count) + ": Processing " + loc.roadID)
        count += 1
        try:
            lat, lng, road_name = get_road_info_from_id(loc.roadID)
            loc.lat = lat
            loc.long = lng
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


class TaxiAvailability(DownloadJson, ConvertHeatmap):
    """Downloads taxi availability JSON."""

    def __init__(self):
        url = "https://api.data.gov.sg/v1/transport/taxi-availability"
        DownloadJson.__init__(self, url)
        ConvertHeatmap.__init__(self)

    def get_time_features(self, json_val):
        features = json_val["features"][0]
        date_time = features["properties"]["timestamp"]
        return date_time, features

    def get_coordinates(self, json_val):
        return json_val["geometry"]["coordinates"]

    def get_properties(self, json_val):
        taxi_count = json_val["properties"]["taxi_count"]
        status = json_val["properties"]["api_info"]["status"]
        return taxi_count, status

    def store_timestamp_coordinates(self, date_time, taxi_count, coordinates):
        created, timestamp, coordinates = super(
            TaxiAvailability, self
        ).store_timestamp_coordinates(date_time, taxi_count, coordinates)
        if created:
            self.store_heatmap(timestamp, coordinates)


@background(queue="taxi-availability")
def start_download():
    # Deletes all previous tasks before running current task
    Task.objects.all().delete()
    logger = getLogger(__name__)
    logger.debug("daemons.download.start_download")
    ta = TaxiAvailability()
    ta.download_timestamps()

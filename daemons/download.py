import requests
import abc
from background_task import background
from logging import getLogger
import datetime
import pytz

from django.utils import dateparse, timezone
from django.conf import settings
from background_task.models import Task
from .models import Timestamp, Coordinate


class DownloadJson:
    """Download one JSON stream using HTTP GET.
    Assume stream has timestamp (when data was last updated).
    Stores all JSON data, with timestamps, in a database.

    Search for missing timestamps within a date_time range.
    Range is (settings.DATE_TIME_START, now).
    For each missing timestamp, download it.
    """

    def __init__(self, url):
        """
        @param url: url to download JSON data from.
        """
        self._url = url
        self._logger = getLogger(__name__)

        # Range of date_time to search missing timestamps.
        self._date_time_start = dateparse.parse_datetime(settings.DATE_TIME_START)
        self._date_time_end = timezone.now()

    @abc.abstractmethod
    def get_time_features(self, json):
        """Given a JSON, extract features and time.
        @return date_time: server-side time that JSON was updated.
        @return features: JSON features to be logged or stored.
        """
        ...

    @abc.abstractmethod
    def get_coordinates(self, json):
        """Given a JSON, extract coordinates.
        @return coordinates: tuple or list of coordinates.
        """
        ...

    @abc.abstractmethod
    def get_properties(self, json):
        """Given a JSON, extract properties.
        @return list of properties.
        """
        ...

    def download(self, url=None):
        """Generic method to download JSON streams.
        @param url: URL to download from. Default: None.
        @return date_time: LTA date_time that JSON was updated.
        """
        json = self.get_json(url)

        # Log errors and exit from function if error.
        # Assume 'code' or 'message' in JSON means error.
        contains_code = "code" in json
        contains_message = "message" in json
        if contains_code or contains_message:
            error_array = []
            if contains_code:
                error_array.append(json["code"])
            if contains_message:
                error_array.append(json["message"])
            self.log(*error_array)
            return

        date_time, features = self.get_time_features(json)
        self.log(*self.get_properties(features))
        coordinates = self.get_coordinates(features)
        self.store(date_time, coordinates)
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

    def store(self, date_time, coordinates):
        """Stores each coordinate with the same unique date_time.
        If date_time is not unique, do not update coordinates.
        @param date_time: LTA date_time that JSON was updated.
        @param coordinates: list of coordinates to be stored.
        """
        timestamp, created = Timestamp.objects.get_or_create(date_time=date_time)
        if created:
            # If created timestamp, store coordinates.
            print("Store {}".format(date_time))
            for coordinate in coordinates:
                Coordinate(
                    lat=coordinate[1], long=coordinate[0], timestamp=timestamp
                ).save()

    def download_missing_timestamps(self):
        """Get current timestamps in database. Identify missing timestamps.
        Timestamps are always more or less 60 seconds apart.
        @return missing: sorted list of missing timestamps.
        """
        timestamps = Timestamp.objects.filter(
            date_time__range=(self._date_time_start, self._date_time_end)
        )

        # Convert to local timezone.
        # Get sorted filtered timestamps. If none, use self._date_time_start and self._date_time_end.
        timezone.activate(pytz.timezone(settings.TIME_ZONE))
        times = sorted([timezone.localtime(x.date_time) for x in timestamps])
        if not times:
            times = [self._date_time_start, self._date_time_end]

        # If current and next timestamps more than missing_seconds apart,
        # then there must be a missing timestamp before (current + missing_seconds).
        missing_seconds = 65
        missing = []
        for i in range(len(times) - 1):
            cur, next = times[i], times[i + 1]

            # Download all contiguous missing timestamps.
            while (next - cur).seconds > missing_seconds:
                missing = cur + datetime.timedelta(seconds=missing_seconds)
                missing = missing.strftime("%Y-%m-%dT%H:%M:%S")
                print("Check {}".format(missing))
                date_time = self.download("{}?date_time={}".format(self._url, missing))
                cur = dateparse.parse_datetime(date_time)

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


class TaxiAvailability(DownloadJson):
    """Downloads taxi availability JSON."""

    def __init__(self):
        url = "https://api.data.gov.sg/v1/transport/taxi-availability"
        super().__init__(url)

    def get_time_features(self, json):
        features = json["features"][0]
        date_timestamp = features["properties"]["timestamp"]
        return date_timestamp, features

    def get_coordinates(self, json):
        return json["geometry"]["coordinates"]

    def get_properties(self, json):
        date_timestamp = json["properties"]["timestamp"]
        taxi_count = json["properties"]["taxi_count"]
        status = json["properties"]["api_info"]["status"]
        return date_timestamp, taxi_count, status


@background(queue="taxi-availability")
def start_download():
    # Deletes all previous tasks before running current task
    Task.objects.all().delete()
    logger = getLogger(__name__)
    logger.debug("daemons.download.start_download")
    ta = TaxiAvailability()
    ta.download_timestamps()

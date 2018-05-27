import requests
import abc
from background_task import background
from logging import getLogger
import datetime
import time
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

    def get_missing_timestamps(self):
        """Get current timestamps in database.
        Identify missing timestamps.
        """
        timestamps = Timestamp.objects.filter(
            date_time__range=(self._date_time_start, self._date_time_end)
        )

        # Convert to local timezone.
        timezone.activate(pytz.timezone(settings.TIME_ZONE))
        times = [timezone.localtime(x.date_time) for x in timestamps]

        # Set seconds to same as start to check for missing times.
        times = [time.replace(second=self._date_time_start.second) for time in times]
        date_set = set(
            self._date_time_start + datetime.timedelta(minutes=m)
            for m in range(
                int((self._date_time_end - self._date_time_start).total_seconds()) // 60
            )
        )
        missing = date_set - set(times)
        return [time.strftime("%Y-%m-%dT%H:%M:%S") for time in missing]

    def download_missing_timestamps(self):
        """Make timestamps in database continuous, in terms of minutes.
        Also, download with current timestamp.
        """
        missing = self.get_missing_timestamps()
        for date_time in sorted(missing):
            print("Check {}".format(date_time))
            self.download("{}?date_time={}".format(self._url, date_time))
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
    ta.download_missing_timestamps()

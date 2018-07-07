import abc
from background_task import background
import datetime
from logging import getLogger
import pytz
import requests
import time

from .convert import ConvertHeatmap, ConvertLocation, ConvertLocationRecords
from .models import Timestamp, Coordinate
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
        json_val = self.get_json_coordinates(url)

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

    def get_json_coordinates(self, url=None):
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
            # If created timestamp, store coordinates.
            print("Store {}".format(date_time))
            for coordinate in coordinates:
                Coordinate(
                    lat=coordinate[1], lng=coordinate[0], timestamp=timestamp
                ).save()
        return created, timestamp, coordinates

    def delete_old_timestamps(self, minutes=43200):
        """Delete timestamps older than 30 days."""
        timestamps = Timestamp.objects.filter(
            date_time__lte=self._date_time_end - datetime.timedelta(minutes=minutes)
        )
        print("Deleting old timestamps:")
        for timestamp in timestamps:
            print(timestamp.date_time)
        print("Finished deleting old timestamps.")
        timestamps.delete()

    def download_missing_timestamps(self):
        """Get current timestamps in database. Identify missing timestamps.
        Timestamps are more or less 60 seconds apart.
        But sometimes they are 90 seconds apart, subsequently 30 seconds apart.
        @return missing: sorted list of missing timestamps.
        """
        # Convert to local timezone.
        timezone.activate(pytz.timezone(settings.TIME_ZONE))

        times = Timestamp.objects.filter(
            date_time__range=(self._date_time_start, self._date_time_end)
        )

        # Sort the filtered timestamps.
        times = sorted(times, key=lambda x: x.date_time)

        # Compare pre to cur, while less than 4 minutes apart, delete and advance cur.
        # Else, advance both pre and cur.
        four_minute_seconds = 235
        five_minute_seconds = 305
        i = 1
        while i < len(times):
            pre, cur = times[i - 1], times[i]

            # For old timestamps.
            if (self._date_time_end - pre.date_time).seconds > five_minute_seconds:

                # Delete every timestamp spaced less than 4 minutes apart.
                while (cur.date_time - pre.date_time).seconds < four_minute_seconds:
                    print(
                        "Sparsing old timestamp {}".format(
                            timezone.localtime(cur.date_time)
                        )
                    )
                    cur.delete()
                    times.pop(i)
                    if i >= len(times):
                        break
                    cur = times[i]
            i += 1

        # Get sorted filtered local timestamps, between start and end inclusive.
        times = (
            [self._date_time_start]
            + [timezone.localtime(x.date_time) for x in times]
            + [self._date_time_end]
        )

        # If pre and cur timestamps more than missing_seconds apart,
        # then there could be a missing timestamp before (current + missing_seconds).
        # If not, then there must be a missing timestamp before (current + missing_seconds_long).
        # If not, raise exception.
        missing_seconds = 65
        missing_seconds_long = 95
        missing = []
        for i in range(1, len(times)):
            pre, cur = times[i - 1], times[i]

            # Split into old and new (less than 5 minutes old) timestamps.
            # For old timestamps.
            if (self._date_time_end - pre).seconds > five_minute_seconds:

                # Download every 5th minute's timestamps.
                while (cur - pre).seconds > five_minute_seconds:
                    missing = self.download_missing_timestamp(pre, five_minute_seconds)
                    pre = missing

            else:

                # Download all contiguous missing timestamps.
                # Advance pre to downloaded timestamp until (cur-pre) gap <= missing_seconds.
                while (cur - pre).seconds > missing_seconds:
                    missing = self.download_missing_timestamp(pre, missing_seconds)

                    # Try longer missing seconds.
                    if pre == missing:
                        missing = self.download_missing_timestamp(
                            pre, missing_seconds_long
                        )
                        if pre == missing:
                            raise Exception(
                                "Gap between adjacent timestamps greater than {} seconds.".format(
                                    missing_seconds_long
                                )
                            )
                    pre = missing

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


class TaxiAvailability(
    DownloadJson, ConvertHeatmap, ConvertLocation, ConvertLocationRecords
):
    """Downloads taxi availability JSON."""

    def __init__(self):
        url = "https://api.data.gov.sg/v1/transport/taxi-availability"
        DownloadJson.__init__(self, url)
        ConvertHeatmap.__init__(self)
        ConvertLocation.__init__(self)
        ConvertLocationRecords.__init__(self)

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
        if settings.INITIALIZE_LOCATIONS:
            if not settings.GRID_CLOSEST_ROADS:
                self.store_locations(coordinates)
        else:
            created, timestamp, coordinates = super(
                TaxiAvailability, self
            ).store_timestamp_coordinates(date_time, taxi_count, coordinates)
            if created:
                self.store_heatmap(timestamp, coordinates)
                self.store_location_records(coordinates, timestamp)


@background(queue="taxi-availability")
def start_download():
    logger = getLogger(__name__)
    logger.debug("daemons.download.start_download")
    ta = TaxiAvailability()
    ta.delete_old_timestamps()
    ta.download_timestamps()

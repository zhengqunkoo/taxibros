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

        # Convert to local timezone.
        timezone.activate(pytz.timezone(settings.TIME_ZONE))

        # Range of date_time to search missing timestamps.
        if settings.DATE_TIME_START:
            self._date_time_start = dateparse.parse_datetime(settings.DATE_TIME_START)
        else:
            self._date_time_start = timezone.localtime(
                timezone.now()
            ) - datetime.timedelta(weeks=1)

        if settings.DATE_TIME_END:
            self._date_time_end = dateparse.parse_datetime(settings.DATE_TIME_END)
        else:
            self._date_time_end = timezone.localtime(timezone.now())

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

    def download(self, url=None, old_timestamp=False):
        """Generic method to download JSON streams.
        @param url: URL to download from. Default: None.
        @param old_timestamp: if True, downloaded timestamp is old.
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
        self.store_timestamp_coordinates(
            date_time, taxi_count, coordinates, old_timestamp=old_timestamp
        )
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

    def store_timestamp_coordinates(
        self, date_time, taxi_count, coordinates, old_timestamp=False
    ):
        """If date_time is not unique, do not do anything.
        Stores each coordinate with the same unique date_time.

        @param date_time: LTA date_time that JSON was updated.
        @param taxi_count: Number of taxis in timestamp.
        @param coordinates: list of coordinates to be stored.
        @param old_timestamp: if True, do not store coordinates.
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
            if not old_timestamp:
                for coordinate in coordinates:
                    Coordinate(
                        lat=coordinate[1], lng=coordinate[0], timestamp=timestamp
                    ).save()
                print("Store {} coordinates".format(date_time))
        return created, timestamp, coordinates

    def delete_old(self):
        self.delete_old_timestamps()
        self.delete_old_coordinates()

    def delete_old_timestamps(self, minutes=10080):
        """Delete timestamps older than 1 week."""
        """
        timestamps = Timestamp.objects.filter(
            date_time__lte=self._date_time_end - datetime.timedelta(minutes=minutes)
        )
        print("Deleting old timestamps:")
        for timestamp in timestamps:
            timestamp.delete()
            print("Deleted timestamp: {}".format(timestamp.date_time))
        print("Finished deleting old timestamps.")
        """

    def delete_old_coordinates(self, minutes=5):
        """Delete coordinates older than 5 minutes."""
        coordinates = Coordinate.objects.filter(
            timestamp__date_time__lte=self._date_time_end
            - datetime.timedelta(minutes=minutes)
        )
        print("Deleting old coordinates:")
        for coordinate in coordinates:
            coordinate.delete()
        print("Finished deleting old coordinates.")

    def download_missing_timestamps(self):
        """Get current timestamps in database. Identify missing timestamps.
        Timestamps are more or less 60 seconds apart.
        But sometimes they are 90 seconds apart, subsequently 30 seconds apart.
        @return missing: sorted list of missing timestamps.
        """
        times = Timestamp.objects.filter(
            date_time__range=(self._date_time_start, self._date_time_end)
        ).order_by("date_time")

        times = list(times)
        self.sparse_old_timestamps(times)

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
        four_minute_seconds = 235
        five_minute_seconds = 305
        for i in range(1, len(times)):
            pre, cur = times[i - 1], times[i]

            # Split into old and new (less than 5 minutes old) timestamps.
            # For old timestamps.
            if (self._date_time_end - pre).total_seconds() > five_minute_seconds:

                # Download every 5th minute's timestamps.
                # Assume if (cur - pre) more than offset, then download succeeds.

                # This fixes timestamps from earlier to later.
                # As cur iterates, all timestamps before cur have 5 minute gap.
                # If 7 minute gap, fill a 5 minute gap and cause a 2 minute gap.
                # 2 minute gap will be fixed in the next call to process_tasks.
                offset = five_minute_seconds
                if (cur - pre).total_seconds() > offset:
                    while True:
                        missing = self.download_missing_timestamp(
                            pre, offset, old_timestamp=True
                        )
                        cur = missing

                        # Break if,
                        #   LTA timestamp fixes time gap.
                        #   LTA timestamp will not be sparsed in next process_tasks.
                        seconds = (cur - pre).total_seconds()
                        if seconds <= offset and seconds > four_minute_seconds:
                            break

                        # Else saved LTA timestamp did not fix time gap.
                        # Delete saved LTA timestamp.
                        print("Undo store {}".format(missing))
                        Timestamp.objects.get(date_time=missing).delete()

                        # Save a dummy (local) time.
                        dummy = pre + datetime.timedelta(seconds=offset)
                        timestamp, created = Timestamp.objects.get_or_create(
                            date_time=dummy, taxi_count=0
                        )
                        if created:
                            print("Store dummy {}".format(dummy))
                            cur = dummy
                        offset += five_minute_seconds

            else:

                # Download every 1 minute's timestamps.
                # Advance pre to downloaded timestamp until (cur-pre) gap <= missing_seconds.
                while (cur - pre).total_seconds() > missing_seconds:
                    missing = self.download_missing_timestamp(
                        pre, missing_seconds, old_timestamp=False
                    )

                    # Try longer missing seconds.
                    if pre == missing:
                        missing = self.download_missing_timestamp(
                            pre, missing_seconds_long, old_timestamp=False
                        )
                        if pre == missing:
                            raise Exception(
                                "Gap between adjacent timestamps greater than {} seconds.".format(
                                    missing_seconds_long
                                )
                            )
                    pre = missing

    def sparse_old_timestamps(self, times):
        """
        Delete every timestamp spaced less than 4 minutes apart.
        @param times: sorted list of all Timestamp objects in database.
        """

        # Compare pre to cur, while less than 4 minutes apart, delete and advance cur.
        # Else, advance both pre and cur.
        four_minute_seconds = 235
        five_minute_seconds = 305
        i = 1
        while i < len(times):
            pre, cur = times[i - 1], times[i]

            # For old timestamps.
            if (
                self._date_time_end - pre.date_time
            ).total_seconds() > five_minute_seconds:

                # Delete every timestamp spaced less than 4 minutes apart.
                while (
                    cur.date_time - pre.date_time
                ).total_seconds() < four_minute_seconds:
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

    def download_missing_timestamp(self, cur, seconds, old_timestamp=False):
        """
        @param cur: current timestamp.
        @param seconds: time after @param cur to query the API with.
        @param old_timestamp: if True, downloaded timestamp is old.
        @return datetime object of LTA timestamp.
        """
        missing = cur + datetime.timedelta(seconds=seconds)
        missing = missing.strftime("%Y-%m-%dT%H:%M:%S")
        print("Check {}".format(missing))
        date_time = self.download(
            "{}?date_time={}".format(self._url, missing), old_timestamp=old_timestamp
        )
        return dateparse.parse_datetime(date_time)

    def download_timestamps(self):
        """Make timestamps in database continuous, in terms of minutes.
        Only download latest timestamp if DATE_TIME_END not defined.
        """
        self.download_missing_timestamps()
        if not settings.DATE_TIME_END:
            print("Check latest")
            self.download(old_timestamp=False)
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

    def store_timestamp_coordinates(
        self, date_time, taxi_count, coordinates, old_timestamp=False
    ):
        if settings.INITIALIZE_LOCATIONS:
            if not settings.GRID_CLOSEST_ROADS:
                self.store_locations(coordinates)
        else:
            created, timestamp, coordinates = super(
                TaxiAvailability, self
            ).store_timestamp_coordinates(
                date_time, taxi_count, coordinates, old_timestamp=old_timestamp
            )
            if created:
                self.store_heatmap(timestamp, coordinates)
                self.store_location_records(coordinates, timestamp)


@background(queue="taxi-availability")
def start_download():
    logger = getLogger(__name__)
    logger.debug("daemons.download.start_download")
    ta = TaxiAvailability()
    ta.delete_old()
    ta.download_timestamps()

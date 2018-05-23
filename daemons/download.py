#!/usr/bin/env python3

import requests
import abc
from background_task import background
from .models import Timestamp, Coordinate
from logging import getLogger
from django.utils import timezone
import datetime
from background_task.models import Task


class DownloadJson:
    """Download one JSON stream using HTTP GET.
    Assume stream has timestamp (when data was last updated).
    When timestamp changes, store data and log errors.
    """

    def __init__(self, folder, url):
        """
        @param folder: folder to log to. Fail if folder does not exist.
        @param url: url to download JSON data from.
        """
        self._url = url
        self._date_and_time = None
        self._logger = getLogger(__name__)

    @abc.abstractmethod
    def get_time_features(self, json):
        """Given a JSON, extract features and time.
        @return date_and_time: server-side time that JSON was updated.
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
        @return properties: string.
        """
        ...

    def download(self):
        """Generic method to download JSON streams.
        Assume logging format in JSON stream.
        """
        response = requests.get(self._url)
        json = response.json()

        # Log errors and exit from function if error.
        # Assume 'code' in json means error.
        # Assume there is 'message' in json with error message.
        if 'code' in json:
            self._logger.debug('{} {}'.format(json['code'], json['message']))
            return

        # Only download when timestamp minute not in db
        self.store_on_time_change(*self.get_time_features(json))

    def store_on_time_change(self, date_and_time, features):
        """Only dump JSON when time updates.
        @param date_and_time: server-side time that JSON was updated.
        @param features: JSON features to be stored or logged.
        """
        # If time minute not in db, add into db (Needed if system fails and restarts/rerunning app)
        times = Timestamp.objects.filter(date_and_time__range = [timezone.now() - datetime.timedelta(minutes=1), timezone.now()])
        if (self._date_and_time == None or self._date_and_time != date_and_time) and times.count() == 0:
            self._date_and_time = date_and_time
            # Log properties of JSON.
            self._logger.debug(self.get_properties(features))
            self.store(self._date_and_time, self.get_coordinates(features))

    def store(self, date_and_time, coordinates):
        """Store each coordinate with same date_and_time.
        @param date_and_time: server-side date_and_time that JSON was updated.
        @param coordinates: list of coordinates to be stored.
        """
        time = datetime.datetime.now()
        time = time.replace(second=0, microsecond=0)
        timestamp = Timestamp(date_and_time=time)
        timestamp.save()
        for coordinate in coordinates:
            Coordinate(
                lat=coordinate[1],
                long=coordinate[0],
                timestamp=timestamp,
            ).save()


class DownloadJsonAuth(DownloadJson):
    """For APIs that need authentication key.
    """

    def __init__(self, folder, url, auth):
        url = urllib.parse.urljoin(
            'https://api.data.gov.sg/v1/transport/busarrival?',
            auth
        )
        super().__init__(folder, url)


class TaxiAvailability(DownloadJson):
    """Downloads taxi availability JSON.
    """

    def __init__(self):
        folder = 'data'
        url = 'https://api.data.gov.sg/v1/transport/taxi-availability'
        super().__init__(folder, url)

    def get_time_features(self, json):
        features = json['features'][0]
        date_and_timestamp = features['properties']['timestamp']
        return date_and_timestamp, features

    def get_coordinates(self, json):
        return json['geometry']['coordinates']

    def get_properties(self, json):
        date_and_timestamp = json['properties']['timestamp']
        taxi_count = json['properties']['taxi_count']
        status = json['properties']['api_info']['status']
        return '{} {} {}'.format(date_and_timestamp, taxi_count, status)


@background(queue='taxi-availability')
def start_download():
    #Deletes all previous tasks before running current task
    Task.objects.all().delete()
    logger = getLogger(__name__)
    logger.debug('daemons.download.start_download')
    ta = TaxiAvailability()
    ta.download()

#!/usr/bin/env python3

import requests
import datetime
import time
import os
import sys
import abc
from background_task import background
from .models import Timestamp, Coordinate
from logging import getLogger

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
        self._timestamp = None
        self._logger = getLogger(__name__)

    @abc.abstractmethod
    def get_timestamp_features(self, json):
        """Given a JSON, extract features and timestamp.
        @return timestamp: server-side time that JSON was updated.
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

        # Only download when timestamp doesn't match.
        self.store_on_timestamp(*self.get_timestamp_features(json))

    def store_on_timestamp(self, timestamp, features):
        """Only dump JSON when timestamp updates.
        @param timestamp: server-side time that JSON was updated.
        @param features: JSON features to be stored or logged.
        """
        # If timestamp changes, update timestamp.
        if self._timestamp == None or self._timestamp != timestamp:
            self._timestamp = timestamp

            # Log properties of JSON.
            self._logger.debug(self.get_properties(features))
            timestamp_model = Timestamp(timestamp=self._timestamp)
            timestamp_model.save()
            self.store(timestamp_model, self.get_coordinates(features))

    def store(self, timestamp_model, coordinates):
        """Store each feature with same timestamp.
        @param timestamp_model: django Model object.
        @param coordinates: list of coordinates to be stored.
        """
        for coordinate in coordinates:
            Coordinate(
                lat=coordinate[1],
                long=coordinate[0],
                timestamp=timestamp_model,
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

    def get_timestamp_features(self, json):
        features = json['features'][0]
        timestamp = features['properties']['timestamp']
        return timestamp, features

    def get_coordinates(self, json):
        return json['geometry']['coordinates']

    def get_properties(self, json):
        timestamp = json['properties']['timestamp']
        taxi_count = json['properties']['taxi_count']
        status = json['properties']['api_info']['status']
        return '{} {} {}'.format(timestamp, taxi_count, status)

from logging import getLogger
logger = getLogger(__name__)
logger.debug(__name__)

@background(schedule=60)
def start_download():
    logger.debug('start_download')
    ta = TaxiAvailability()
    ta.download()

#!/usr/bin/env python3

import requests
import bson
import datetime
import time
import os
import sys
from argparse import ArgumentParser

class DownloadJson:
    """Download one JSON stream using HTTP GET.
    The stream is stored in subfolder, named with the URL of stream.
    Assume stream has timestamp (when data was last updated).
    When timestamp changes, store data and log errors.
    """

    def __init__(self, folder, url):
        """
        @param folder: folder to download JSON data to.
            Fail if folder does not exist.
        @param url: url to download JSON data from.
        """
        self._url = url
        self._timestamp = None
        if not os.path.exists(folder):
            print('{} folder does not exist, please create it'.format(folder))
            sys.exit(-1)

        # Make subfolder if subfolder does not exist.
        # Subfolder is last part of URL.
        self._subfolder = os.path.join(folder, url.split('/')[-1])
        if not os.path.exists(self._subfolder):
            os.makedirs(self._subfolder)
        self._log = os.path.join(self._subfolder, 'log.md')

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
            self.write_log(json['code'], json['message'])
            return

        # Only download when timestamp doesn't match.
        features = json['features'][0]
        timestamp = features['properties']['timestamp']
        self.store_on_timestamp(timestamp, features)

    def store_on_timestamp(self, timestamp, features):
        """Only dump JSON when timestamp updates.
        @param timestamp: server-side time that JSON was updated.
        @param features: JSON features to be stored.
        """
        # If timestamp changes, update timestamp.
        if self._timestamp == None or self._timestamp != timestamp:
            self._timestamp = timestamp

            # Dump JSON and log health.
            self.dump_json(features)
            self.write_log(timestamp, features['properties']['api_info']['status'])

    def dump_json(self, features):
        """Write JSON as BSON to file.
        @param features: JSON features to be stored.
        """
        # Write as compressed BSON.
        with open(os.path.join(self._subfolder, self._timestamp), 'wb') as f:
            f.write(bson.dumps(features))

    def write_log(self, string_one, string_two):
        """Logs two strings with current client-side time.
        @param string_one: first string to be logged.
        @param string_two: second string to be logged.
        """
        with open(self._log, 'a') as f:
            f.write('{} {} {}\n'.format(datetime.datetime.now(),
                                        string_one, string_two))


if __name__ == "__main__":
    parser = ArgumentParser(description='Instantly query taxi arrival times')
    parser.add_argument('-folder', type=str, nargs='?',
                        default='data',
                        help='folder to download JSON data to')
    parser.add_argument('-url', type=str, nargs='?',
                        default='https://api.data.gov.sg/v1/transport/taxi-availability',
                        help='url to download JSON data from')

    args = parser.parse_args()
    dj = DownloadJson(args.folder, args.url)
    # Download forever
    while True:
        dj.download()
        time.sleep(40)

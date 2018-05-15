#!/usr/bin/env python3

import requests
import bson
import datetime
import time
import os

class DownloadJson:

    def __init__(self, api):
        self._url = 'https://api.data.gov.sg/v1/transport/{}'.format(api)
        self._folder = api + '/'
        self._timestamp = None
        self._log = self._folder + 'log.md'

        # Download all files into a folder.
        if not os.path.exists(self._folder):
            os.makedirs(self._folder)

    def download(self):
        response = requests.get(self._url)
        json = response.json()

        # Log errors.
        if 'code' in json:
            with open(self._log, 'a') as f:
                f.write('{} {} {} error\n'.format(datetime.datetime.now(), json['code'], json['message']))
            return

        # Only download when timestamp doesn't match.
        features = json['features'][0]
        timestamp = features['properties']['timestamp']
        if self._timestamp == None or self._timestamp != timestamp:
            self._timestamp = self._folder + timestamp

            # Write as compressed BSON.
            with open(self._timestamp, 'wb') as f:
                f.write(bson.dumps(features))

            # Log health.
            with open(self._log, 'a') as f:
                f.write('{} {} {}\n'.format(datetime.datetime.now(), timestamp, features['properties']['api_info']['status']))


if __name__ == '__main__':
    apis = ['taxi-availability']
    djs = [DownloadJson(api) for api in apis]
    while True:
        [dj.download() for dj in djs]
        time.sleep(40)

import datetime
import pytz
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase, override_settings
from django.utils import timezone
from daemons.download import DownloadJson, TaxiAvailability
from daemons.models import Timestamp, Location


@patch("daemons.download.DownloadJson.get_json")
class DownloadApiTest(TestCase):
    """Tests if daemon extracts correct information from API.
    Mock API calls in DownloadJson.
    """

    @classmethod
    def setUpTestData(cls):
        """Test functionality using TaxiAvailability.
        Override init with mock superclass.
        Define some mock JSONs returned from API.
        """
        cls._json_unavailable = {"message": "Forbidden"}
        cls._json_error = {"code": 0, "message": "string"}
        cls._json_no_results = {
            "api_info": {"status": "healthy"},
            "message": "no results found",
        }
        cls._json_results = {
            "type": "FeatureCollection",
            "crs": {
                "type": "link",
                "properties": {
                    "href": "http://spatialreference.org/ref/epsg/4326/ogcwkt/",
                    "type": "ogcwkt",
                },
            },
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "MultiPoint",
                        "coordinates": [
                            [103.99528, 1.3754],
                            [104.00055, 1.3809],
                            [104.00057, 1.38101],
                            [104.00072, 1.3807],
                            [104.00098, 1.38424],
                        ],
                    },
                    "properties": {
                        "timestamp": "2017-05-15T13:02:57+08:00",
                        "taxi_count": 5,
                        "api_info": {"status": "healthy"},
                    },
                }
            ],
        }

    @patch("daemons.download.DownloadJson.log")
    def test_api_healthy(self, mock_log, mock_get_json):
        """API health indicates API is behaving normally."""
        mock_get_json.return_value = self._json_results
        TaxiAvailability().download()
        mock_log.assert_called_with("2017-05-15T13:02:57+08:00", 5, "healthy")

    @patch("daemons.download.DownloadJson.log")
    def test_api_no_results(self, mock_log, mock_get_json):
        """If date_time does not exist, API returns no results."""
        mock_get_json.return_value = self._json_no_results
        TaxiAvailability().download()
        mock_log.assert_called_with("no results found")

    @patch("daemons.download.DownloadJson.log")
    def test_api_error(self, mock_log, mock_get_json):
        """If API rate limit exceeded, returns error."""
        mock_get_json.return_value = self._json_error
        TaxiAvailability().download()
        mock_log.assert_called_with(0, "string")

    @patch("daemons.download.DownloadJson.log")
    def test_api_unavailable(self, mock_log, mock_get_json):
        """Due to maintenance activities, please be informed that all APIs
        will be unavailable, no data available or no updated data.
        """
        mock_get_json.return_value = self._json_unavailable
        TaxiAvailability().download()
        mock_log.assert_called_with("Forbidden")


class DownloadDatabaseTest(TestCase):
    """Tests daemon's interactions with database."""

    @classmethod
    def setUpTestData(cls):
        """Activate timezone for DATE_TIME_START."""
        from django.conf import settings

        timezone.activate(pytz.timezone(settings.TIME_ZONE))
        cls._json_results = {
            "type": "FeatureCollection",
            "crs": {
                "type": "link",
                "properties": {
                    "href": "http://spatialreference.org/ref/epsg/4326/ogcwkt/",
                    "type": "ogcwkt",
                },
            },
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "MultiPoint",
                        "coordinates": [
                            [103.99528, 1.3754],
                            [104.00055, 1.3809],
                            [104.00057, 1.38101],
                            [104.00072, 1.3807],
                            [104.00098, 1.38424],
                        ],
                    },
                    "properties": {
                        "timestamp": "2017-05-15T13:02:57+08:00",
                        "taxi_count": 5,
                        "api_info": {"status": "healthy"},
                    },
                }
            ],
        }
        cls._json_results2 = {
            "type": "FeatureCollection",
            "crs": {
                "type": "link",
                "properties": {
                    "href": "http://spatialreference.org/ref/epsg/4326/ogcwkt/",
                    "type": "ogcwkt",
                },
            },
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "MultiPoint",
                        "coordinates": [
                            [103.99528, 1.3754],
                            [104.00055, 1.3809],
                            [104.00057, 1.38101],
                            [104.00072, 1.3807],
                            [104.00098, 1.38424],
                        ],
                    },
                    "properties": {
                        "timestamp": "2017-05-15T13:02:58+08:00",  # To simulate a second run
                        "taxi_count": 5,
                        "api_info": {"status": "healthy"},
                    },
                }
            ],
        }

        cls._nearest_road_results = {
            "snappedPoints": [
                {
                    "location": {
                        "latitude": 1.343211721179933,
                        "longitude": 103.76092847271761,
                    },
                    "originalIndex": 1,
                    "placeId": "ChIJqSxg_mgQ2jERVYEAKmGw0aw",
                },
                {
                    "location": {
                        "latitude": 1.3449623148300323,
                        "longitude": 103.76088042484533,
                    },
                    "originalIndex": 2,
                    "placeId": "ChIJNWdwM2gQ2jER0Gamoz7a4bU",
                },
                {
                    "location": {
                        "latitude": 1.3449623148300323,
                        "longitude": 103.76088042484533,
                    },
                    "originalIndex": 2,
                    "placeId": "ChIJNWdwM2gQ2jER0Wamoz7a4bU",
                },
            ]
        }
        cls._closest_road_result1 = ["0", "1", "2"]
        cls._closest_road_result2 = ["2", "3", "4"]

    # Make start_date_time always one minute before end_date_time (now).
    @override_settings(
        DATE_TIME_START=timezone.localtime(
            (timezone.now() - datetime.timedelta(minutes=1))
        ).strftime("%Y-%m-%dT%H:%M:%S%z")
    )
    def setUp(self):
        """Create TaxiAvailability class.
        Filter always returns a queryset with a one minute time range.
        """
        self._ta = TaxiAvailability()

    @patch("daemons.download.DownloadJson.get_json")
    def test_unique_timestamp(self, mock_get_json):
        """Download one timestamp. Download the same timestamp again.
        On second download, Timestamp.save() shouldn't be called.
        """
        mock_get_json.return_value = self._json_results
        self.assertEquals(Timestamp.objects.all().count(), 0)
        self._ta.download()
        self.assertEquals(Timestamp.objects.all().count(), 1)
        self._ta.download()
        self.assertEquals(Timestamp.objects.all().count(), 1)

    @patch("daemons.download.DownloadJson.get_json")
    def test_process_closest_roads(self, mock_get_json):
        """Check if closest roads are returned in the right format given a json response."""
        mock_get_json.return_value = self._nearest_road_results
        expected = [None, "ChIJqSxg_mgQ2jERVYEAKmGw0aw", "ChIJNWdwM2gQ2jER0Wamoz7a4bU"]
        actual = self._ta.get_closest_roads_api([(0, 0), (1, 1), (2, 2)])
        self.assertEquals(expected, actual)

    @patch("daemons.convert.ConvertLocation.get_closest_roads_api")
    @patch("daemons.download.DownloadJson.get_json")
    def test_unique_location(self, mock_get_json, mock_get_closest_roads):
        """Download two timestamps, each with locations that both share and are unique to each
        timestamp. The right number should be returned after each call"""

        self.assertEquals(Location.objects.all().count(), 0)
        # First download
        mock_get_json.return_value = self._json_results
        mock_get_closest_roads.return_value = self._closest_road_result1
        self._ta.download()
        self.assertEquals(Location.objects.all().count(), 3)
        # Second download
        mock_get_json.return_value = self._json_results2
        mock_get_closest_roads.return_value = self._closest_road_result2
        self._ta.download()
        self.assertEquals(Location.objects.all().count(), 5)

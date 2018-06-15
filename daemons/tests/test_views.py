import datetime
import pytz
from unittest.mock import patch
from requests import Response
from django.conf import settings
from django.test import TestCase, override_settings
from django.utils import timezone
from daemons.views import get_path_geom, get_count_at_road
from daemons.models import Timestamp, Location, LocationRecord


class GenLocTest(TestCase):
    """Tests if GenLoc and its associated helper methods return the right values"""

    @classmethod
    def setUpTestData(cls):
        cls._path_geom = Response()
        cls._path_geom.status_code = 200

        cls._path_geom_error = Response()
        cls._path_geom_error.status_code = 500

        cls._path_geom_ok_val = {
            "status_message": "Found route between points",
            "route_geometry": "mock_route_geom",
            "status": 0,
            "route_instructions": [],
            "route_name": [""],
            "route_summary": {
                "start_point": "",
                "end_point": "",
                "total_time": 523,
                "total_distance": 725,
            },
        }

        cls._path_geom_error_val = {
            "error": "Unable to get walk path: Error with status code: 400"
        }

    def setUp(self):
        """Initialize the location coordinates as well as locationrecords
        """
        loc1 = Location(roadID="1")
        loc2 = Location(roadID="2")
        loc3 = Location(roadID="3")
        timestamp1 = Timestamp(date_time=datetime.datetime.now(), taxi_count=3)
        timestamp2 = Timestamp(
            date_time=datetime.datetime.now() - datetime.timedelta(minutes=1),
            taxi_count=1,
        )

        loc1.save()
        loc2.save()
        loc3.save()
        timestamp1.save()
        timestamp2.save()

        LocationRecord(count=1, location=loc1, timestamp=timestamp1).save()
        LocationRecord(count=2, location=loc2, timestamp=timestamp1).save()

        LocationRecord(count=1, location=loc1, timestamp=timestamp2).save()

    @patch("requests.Response.json")
    @patch("requests.get")
    def test_get_path_geom(self, mock_requests_get, mock_response_json):
        """Tests that the right value extracted from json for path_geom, or the None returned on error
        """
        mock_requests_get.return_value = self._path_geom
        mock_response_json.return_value = self._path_geom_ok_val
        result = get_path_geom(1, 2, 3, 4)
        self.assertEquals(result, "mock_route_geom")

        mock_response_json.return_value = self._path_geom_error_val
        result = get_path_geom(1, 2, 3, 4)
        self.assertEquals(result, None)

        mock_requests_get.return_value = self._path_geom_error
        result = get_path_geom(1, 2, 3, 4)
        self.assertEquals(result, None)

    def test_get_count_at_road(self):
        """Tests that the right count is retrieved from road"""
        loc1 = Location.objects.get(pk="1")
        res = get_count_at_road(loc1)
        self.assertEquals(res, 2)

        loc2 = Location.objects.get(pk="2")
        res = get_count_at_road(loc2)
        self.assertEquals(res, 2)

        loc3 = Location.objects.get(pk="3")
        res = get_count_at_road(loc3)
        self.assertEquals(res, 0)

        res = get_count_at_road(None)
        self.assertEquals(res, 0)

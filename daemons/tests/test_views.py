import datetime
import pytz
from unittest.mock import patch
from requests import Response
from django.conf import settings
from django.test import TestCase, override_settings
from django.utils import timezone
from daemons.views import get_path_geom
from daemons.models import Timestamp, Location


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

    @patch("requests.Response.json")
    @patch("requests.get")
    def test_get_path_geom(self, mock_requests_get, mock_response_json):
        """Tests that the right value extracted from json for path_geom
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

import datetime
from unittest.mock import patch
from requests import Response
from django.test import TestCase
from django.utils import timezone
from daemons.views import (
    get_path_data,
    get_count_at_road,
    get_closest_roads,
    get_best_road,
)
from daemons.models import Timestamp, Location, LocationRecord
from scipy.spatial import KDTree


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
            "route_instructions": [
                [
                    "Head",
                    "",
                    8,
                    "1.330668,103.912984",
                    6,
                    "8m",
                    "North West",
                    "North",
                    "walking",
                    "Head Northwest",
                ],
                [
                    "Right",
                    "",
                    6,
                    "1.330727,103.912956",
                    5,
                    "6m",
                    "North East",
                    "North West",
                    "walking",
                    "Turn Right",
                ],
            ],
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
        self._loc1 = Location(roadID="1", lat=1.345042, lng=103.759904)  # Inside 500m
        self._loc2 = Location(roadID="2", lat=1.338646, lng=103.741639)  # Outside 500m
        self._loc3 = Location(roadID="3", lat=1.344474, lng=103.759668)  # Inside 500m
        self._loc4 = Location(roadID="4")
        timestamp1 = Timestamp(date_time=datetime.datetime.now(), taxi_count=3)
        timestamp2 = Timestamp(
            date_time=datetime.datetime.now() - datetime.timedelta(minutes=1),
            taxi_count=1,
        )

        self._loc1.save()
        self._loc2.save()
        self._loc3.save()
        self._loc4.save()
        timestamp1.save()
        timestamp2.save()

        LocationRecord(count=1, location=self._loc1, timestamp=timestamp1).save()
        LocationRecord(count=2, location=self._loc2, timestamp=timestamp1).save()
        LocationRecord(count=1, location=self._loc1, timestamp=timestamp2).save()

        self._locs = [loc for loc in Location.objects.all()]
        self._locs = list(filter(lambda x: x.lat != 0, self._locs))
        self._tree = KDTree(
            list(map(lambda x: (float(x.lat), float(x.lng)), self._locs)), leafsize=3000
        )
        self._radius = 500

    @patch("requests.Response.json")
    @patch("requests.get")
    def test_get_path_data(self, mock_requests_get, mock_response_json):
        """Tests that the right value extracted from json for path_geom, or the None returned on error
        """
        mock_requests_get.return_value = self._path_geom
        mock_response_json.return_value = self._path_geom_ok_val
        geom, instructions, time, dist = get_path_data(1, 2, 3, 4)
        self.assertEquals(geom, "mock_route_geom")
        self.assertEquals(
            instructions,
            [
                [
                    "Head",
                    "",
                    8,
                    "1.330668,103.912984",
                    6,
                    "8m",
                    "North West",
                    "North",
                    "walking",
                    "Head Northwest",
                ],
                [
                    "Right",
                    "",
                    6,
                    "1.330727,103.912956",
                    5,
                    "6m",
                    "North East",
                    "North West",
                    "walking",
                    "Turn Right",
                ],
            ],
        )
        self.assertEquals(time, 523)
        self.assertEquals(dist, 725)

        mock_response_json.return_value = self._path_geom_error_val
        result, a, b = get_path_data(1, 2, 3, 4)
        self.assertEquals(result, None)

        mock_requests_get.return_value = self._path_geom_error
        result, a, b = get_path_data(1, 2, 3, 4)
        self.assertEquals(result, None)

    def test_get_count_at_road(self):
        """Tests that the right count is retrieved from road"""
        res = get_count_at_road(self._loc1)
        self.assertEquals(res, 2)

        res = get_count_at_road(self._loc2)
        self.assertEquals(res, 2)

        res = get_count_at_road(self._loc3)
        self.assertEquals(res, 0)

        res = get_count_at_road(None)
        self.assertEquals(res, 0)

    def test_get_closest_roads(self):
        """Checks kdtree, before ensuring the right roads are retrived"""
        # TODO: create a new test initialize kdtree function
        self.assertEquals(self._locs, [self._loc1, self._loc2, self._loc3])

        actual = get_closest_roads(
            1.345042, 103.759904, self._locs, self._tree, self._radius
        )
        expected = [self._loc1, self._loc3]

        self.assertEquals(len(actual), len(expected))
        self.assertEquals(set(actual), set(expected))

    @patch("daemons.views.get_closest_roads")
    def test_get_best_road(self, mock_get_closest_roads):
        """Checks get_best_road returns road with largest count within 500m"""
        mock_get_closest_roads.return_value = get_closest_roads(
            1.345042, 103.759904, self._locs, self._tree, self._radius
        )
        actual = get_best_road(1.345042, 103.759904, self._radius)
        expected = self._loc1
        self.assertEquals(actual, expected)

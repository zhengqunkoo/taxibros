from .models import Location
from .convert import ConvertRoad


class GridCoordinates:
    def __init__(self, ll_lat=1.205, ll_lng=103.605, ur_lat=1.4705, ur_lng=104.95):
        """Define bounding box of island."""
        self._ll_lat = ll_lat
        self._ll_lng = ll_lng
        self._ur_lat = ur_lat
        self._ur_lng = ur_lng

    def interpolate(self, ll_lat, ll_lng, ur_lat, ur_lng, resolution=1000000):
        """
        @param resolution: 10^n, where n is the last decimal place of output coordinates.
            Must be at least the decimal place of inputs @param ll_lat, ll_lng, ur_lat, ur_lng.
        """
        if (
            ll_lat < self._ll_lat
            or ll_lng < self._ll_lng
            or ur_lat < self._ur_lat
            or ur_lng < self._ur_lng
        ):
            print("Error: selection outside of Singapore.")
            return
        if ll_lat >= ur_lat or ll_lng >= ur_lng:
            print("Error: make sure (ll_lat, ll_lng) < (ur_lat, ur_lng).")
            return

        print(
            "Number of grid points: {}.".format(
                (ur_lng * resolution - ll_lng * resolution)
                * (ur_lat * resolution - ll_lat * resolution)
            )
        )
        print(
            "Percentage of island area: {}.".format(
                (ur_lng - ll_lng)
                * (ur_lat - ll_lat)
                / (self._ur_lng - self._ll_lng)
                * (self._ur_lat - self._ll_lat)
            )
        )

        return [
            [lng / resolution, lat / resolution]
            for lng in range(ll_lng * resolution, ur_lng * resolution)
            for lat in range(ll_lat * resolution, ur_lat * resolution)
        ]

    def start(self, ll_lat, ll_lng, ur_lat, ur_lng, resolution=1000000):
        """Save Road ID of interpolated coordinates as Location model.
        Save model with defaults (to be set by convert.process_location_coordinates).
        """
        for road_id in ConvertRoad.get_closest_roads(
            self.interpolate(ll_lat, ll_lng, ur_lat, ur_lng, resolution=1000000)
        ):
            Location(roadID=road_id).save()

from .models import Location


class GridCoordinates:
    def __init__(self, ll_lat=1.205, ll_lng=103.605, ur_lat=1.4705, ur_lng=104.05):
        """Define bounding box of island."""
        self._ll_lat = ll_lat
        self._ll_lng = ll_lng
        self._ur_lat = ur_lat
        self._ur_lng = ur_lng

    def interpolate(self, ll_lat, ll_lng, ur_lat, ur_lng, xbins=531, ybins=890):
        """
        @param xbins, ybins: number of bins along each of the x-, y-axes.
            Default:
                Width and height of Singapore in terms of lng, lat.
                width, height: 0.445, 0.2655 (lng, lat).
                xbins, ybins: 890, 531 is 3.5 decimal place accuracy.
                See https://en.wikipedia.org/wiki/Decimal_degrees.

                Excludes some islands (assume no taxis in islands).
                Lower left: 1.205, 103.605 (lat, lng).
                Upper right: 1.4705, 104.05 (lat, lng).
        """
        if (
            ll_lat < self._ll_lat
            or ll_lng < self._ll_lng
            or ur_lat > self._ur_lat
            or ur_lng > self._ur_lng
        ):
            print("Error: selection outside of Singapore.")
            return
        if ll_lat >= ur_lat or ll_lng >= ur_lng:
            print("Error: make sure (ll_lat, ll_lng) < (ur_lat, ur_lng).")
            return

        print(
            "Number of grid points: {}.".format(
                (ur_lng * ybins - ll_lng * ybins) * (ur_lat * xbins - ll_lat * xbins)
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
            [lng / ybins, lat / xbins]
            for lng in range(int(ll_lng * ybins), int(ur_lng * ybins))
            for lat in range(int(ll_lat * xbins), int(ur_lat * xbins))
        ]

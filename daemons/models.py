from django.db import models


class Timestamp(models.Model):
    """Model representing time.
    Assume time is unique.
    """

    date_time = models.DateTimeField()
    taxi_count = models.IntegerField(help_text="Number of taxis at this timestamp.")

    def __str__(self):
        """
        String for representing the Model object.
        """
        return "{} {}".format(self.date_time, self.taxi_count)


class Coordinate(models.Model):
    """Model representing a coordinate recorded at timestamp.
    Assume coordinate has maximum accuracy of 10cm.
    """

    lat = models.DecimalField(max_digits=9, decimal_places=6, help_text="Latitude")
    long = models.DecimalField(max_digits=9, decimal_places=6, help_text="Longitude")
    timestamp = models.ForeignKey(Timestamp, on_delete=models.CASCADE)

    def __str__(self):
        """
        String for representing the Model object (in Admin site etc.).
        """
        return "{},{}".format(self.lat, self.long)


class Location(models.Model):
    """Model representing a location"""

    roadID = models.CharField(max_length=27, primary_key=True)
    road_name = models.CharField(max_length=27, default="")
    lat = models.DecimalField(
        max_digits=9, decimal_places=6, help_text="Latitude", default=0
    )
    long = models.DecimalField(
        max_digits=9, decimal_places=6, help_text="Longitude", default=0
    )

    def __str__(self):
        return self.roadID


class LocationRecord(models.Model):
    """Model representing a location and a record of the number of taxis
    """

    count = models.PositiveIntegerField()
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    timestamp = models.ForeignKey(Timestamp, on_delete=models.CASCADE)

    def __str__(self):
        """
        String for representing a location record
        """
        return "{}:{}:".format(str(timestamp), str(location))


class Heatmap(models.Model):
    """Model representing one intensity.
    It aligns the heatmap properly on the map, using the tile as anchor.

    Similar structure to Coordinate model, but this Heatmap model is needed.
    Otherwise if use Coordinate to store Heatmaps, will taint coordinate queries.
        Coordinate sets of timestamps will return Heatmaps too.
        Heatmap might be a distinct coordinate.
        An extra coordinate might be returned. This is undesirable.
    """

    left = models.DecimalField(max_digits=9, decimal_places=6, help_text="Left extent")
    right = models.DecimalField(
        max_digits=9, decimal_places=6, help_text="Right extent"
    )
    bottom = models.DecimalField(
        max_digits=9, decimal_places=6, help_text="Bottom extent"
    )
    top = models.DecimalField(max_digits=9, decimal_places=6, help_text="Top extent")
    xbins = models.PositiveIntegerField(help_text="Number of bins in x-direction.")
    ybins = models.PositiveIntegerField(help_text="Number of bins in y-direction.")
    timestamp = models.OneToOneField(Timestamp, on_delete=models.CASCADE)

    def __str__(self):
        """
        String for representing the Model object (in Admin site etc.).
        """
        return "{},{},{},{}".format(
            self.left, self.right, self.bottom, self.top, self.xbins, self.ybins
        )


class Heattile(models.Model):
    """Model representing a tile on a heatmap.
    Compressed from coordinates by binning nearby coordinates together.

    There are some additional attributes:
        timestamp allows users to lookup heatmaps using that timestamp.
        lower_left is coordinate of lower-leftmost heattile.
            Not necessarily same as lower-leftmost Coordinate model.
            It is an anchor for aligning the heatmap on the map.
    """

    intensity = models.PositiveIntegerField(
        help_text="Intensity at one unindexed tile of heatmap."
    )
    x = models.PositiveIntegerField(help_text="X-coordinate of tile of heatmap.")
    y = models.PositiveIntegerField(help_text="Y-coordinate of tile of heatmap.")
    heatmap = models.ForeignKey(Heatmap, on_delete=models.CASCADE)

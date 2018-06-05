from django.db import models


class Timestamp(models.Model):
    """Model representing time.
    Assume time is unique.
    """
    date_time = models.DateTimeField()

    def __str__(self):
        """
        String for representing the Model object.
        """
        return str(self.date_time)


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


class Heatmap(models.Model):
    """Model representing one intensity.
    Compressed from coordinates by binning nearby coordinates together.
    """
    intensity = models.IntegerField(
        help_text="Intensity at one unindexed tile of heatmap."
    )
    x = models.IntegerField(help_text="X-coordinate of tile of heatmap.")
    y = models.IntegerField(help_text="Y-coordinate of tile of heatmap.")
    timestamp = models.ForeignKey(Timestamp, on_delete=models.CASCADE)

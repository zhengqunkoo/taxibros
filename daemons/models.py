from django.db import models


class Timestamp(models.Model):
    """Model representing time.
    Assume time is unique.
    """
    date_time = models.DateTimeField()
    

class Coordinate(models.Model):
    """Model representing a coordinate recorded at timestamp.
    Assume coordinate has maximum accuracy of 10cm.
    """
    lat = models.DecimalField(max_digits=9, decimal_places=6, help_text="Latitude")
    long = models.DecimalField(max_digits=9, decimal_places=6, help_text="Longitude")
    timestamp = models.ForeignKey(Timestamp, on_delete=models.CASCADE, null=True)

    def __str__(self):
        """
        String for representing the Model object (in Admin site etc.).
        """
        return "{},{}".format(self.lat, self.long)

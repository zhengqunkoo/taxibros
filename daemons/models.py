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

class Location(models.Model):
    """Model representing a location"""
    location = models.CharField(max_length = 27)
    def __str__(self):
        return self.location

class LocationRecord(models.Model):
    """Model representing a location and a record of the number of taxis
    """
    count = models.PositiveIntegerField()
    location = models.ForeignKey(Location,  on_delete = models.CASCADE)
    timestamp = models.ForeignKey(Timestamp, on_delete = models.CASCADE)
    def __str__(self):
        """
        String for representing a location record
        """
        return "{}:{}:".format(str(timestamp), str(location))

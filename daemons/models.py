from django.db import models
from django.urls import reverse


class Timestamp(models.Model):
    """Model representing timestamp.
    Assume timestamp is unique.
    """
    timestamp = models.DateTimeField()
    
    def __str__(self):
        """
        String for representing the Model object.
        """
        return str(self.timestamp)
    
    
    def get_absolute_url(self):
        """Returns the url to access a detail record for this timestamp."""
        return reverse('timestamp-detail', args=[str(self.id)])


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

import uuid
from django.db import models


class Record(models.Model):
    """Model representing one recording."""

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, help_text="Unique ID for recording."
    )
    time = models.FloatField(help_text="Time elapsed.")
    width = models.IntegerField(help_text="Width of screen.")
    height = models.IntegerField(help_text="Height of screen.")

    def __str__(self):
        """String for representing the Model object."""
        return "{} {} {},{}".format(self.id, self.time, self.width, self.height)


class Frame(models.Model):
    """Model of frames recorded by musjs."""

    mode = models.CharField(max_length=1, help_text="Mode of mouse frame.")
    x = models.IntegerField(help_text="X-coordinate of mouse.")
    y = models.IntegerField(help_text="Y-coordinate of mouse.")
    record = models.ForeignKey(Record, on_delete=models.CASCADE)

    def __str__(self):
        """String for representing the Model object."""
        return "{} {} {}".format(self.mode, self.x, self.y)

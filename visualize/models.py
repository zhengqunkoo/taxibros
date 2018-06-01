from django.db import models
from daemons.models import Timestamp


class Heatmap(models.Model):
    """Model representing one intensity.
    Compressed from coordinates by binning nearby coordinates together.
    """
    intensity = models.FloatField(
        help_text="Intensity at one unindexed tile of heatmap."
    )
    x = models.IntegerField(help_text="X-coordinate of tile of heatmap.")
    y = models.IntegerField(help_text="Y-coordinate of tile of heatmap.")
    timestamp = models.ForeignKey(Timestamp, on_delete=models.CASCADE)

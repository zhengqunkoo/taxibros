from django.contrib import admin

from .models import Heatmap


@admin.register(Heatmap)
class HeatmapAdmin(admin.ModelAdmin):
    list_display = ("intensity", "x", "y", "timestamp")

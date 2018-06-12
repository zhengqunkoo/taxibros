from django.contrib import admin

from .models import Timestamp, Coordinate, Heatmap, Heattile


def delete_selected(modeladmin, request, queryset):
    queryset.delete()


@admin.register(Timestamp)
class TimestampAdmin(admin.ModelAdmin):
    list_display = ("date_time", "taxi_count")
    actions = (delete_selected,)


@admin.register(Coordinate)
class CoordinateAdmin(admin.ModelAdmin):
    list_display = ("lat", "lng", "timestamp")


@admin.register(Heatmap)
class HeatmapAdmin(admin.ModelAdmin):
    list_display = ("left", "right", "bottom", "top", "xbins", "ybins", "timestamp")


@admin.register(Heattile)
class HeattileAdmin(admin.ModelAdmin):
    list_display = ("intensity", "x", "y", "heatmap")

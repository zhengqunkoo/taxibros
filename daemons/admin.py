from django.contrib import admin

from .models import Timestamp, Coordinate


def delete_selected(modeladmin, request, queryset):
    queryset.delete()


@admin.register(Timestamp)
class TimestampAdmin(admin.ModelAdmin):
    list_display = ("date_time",)
    actions = (delete_selected,)


@admin.register(Coordinate)
class CoordinateAdmin(admin.ModelAdmin):
    list_display = ("lat", "long")

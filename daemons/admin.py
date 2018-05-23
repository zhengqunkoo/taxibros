from django.contrib import admin

from .models import Timestamp, Coordinate


@admin.register(Timestamp)
class TimestampAdmin(admin.ModelAdmin):
    list_display = ('date_time', 'coordinates')

    def coordinates(self, obj):
        size = 3
        coordinates = Coordinate.objects.filter(timestamp=obj)
        return ', '.join([str(c) for c in coordinates[:size]]) \
                + '... ({} total)'.format(len(coordinates))


@admin.register(Coordinate)
class CoordinateAdmin(admin.ModelAdmin):
    list_display = ('lat', 'long')

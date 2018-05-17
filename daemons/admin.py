from django.contrib import admin

from .models import Timestamp, Coordinate


@admin.register(Timestamp)
class TimestampAdmin(admin.ModelAdmin):
    list_display = ('timestamp',)


@admin.register(Coordinate)
class CoordinateAdmin(admin.ModelAdmin):
    list_display = ('lat', 'long')
    fieldsets = (
        (None, {
            'fields': ('lat', 'long'),
        }),
    )

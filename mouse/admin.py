from django.contrib import admin

from .models import Record, Frame


def delete_selected(modeladmin, request, queryset):
    queryset.delete()


@admin.register(Record)
class RecordAdmin(admin.ModelAdmin):
    list_display = ("id", "time", "width", "height", "ua_string")
    actions = (delete_selected,)


@admin.register(Frame)
class FrameAdmin(admin.ModelAdmin):
    list_display = ("mode", "x", "y")

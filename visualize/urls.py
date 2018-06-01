from django.urls import path
from django.conf import settings
from . import views

app_name = "visualize"
urlpatterns = [
    path("", views.index, name="index"),
    path("heatmap", views.heatmap, name="heatmap"),
    path("genTime.js", views.gen_time_js, name="genTime"),
    path("genLoc.js", views.gen_loc_js, name="genLoc"),
    path("map.js", views.map_js, name="map"),
]

from django.urls import path
from django.conf import settings
from . import views

app_name = "visualize"
urlpatterns = [
    path("", views.index, name="index"),
    path("genHeatmap.js", views.gen_heatmap_js, name="genHeatmap"),
    path("genTime.js", views.gen_time_js, name="genTime"),
    path("genLoc.js", views.gen_loc_js, name="genLoc"),
    path("map.js", views.map_js, name="map"),
    path("slider.js", views.slider_js, name="slider"),
    path("table.js", views.table_js, name="table"),
    path("genChart.js", views.get_chart_data_js, name="chart"),
]

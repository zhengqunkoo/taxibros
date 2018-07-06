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
    path("chart.js", views.chart_js, name="chart"),
    path("genChart.js", views.gen_chart_js, name="genChart"),
    path("genCost.js", views.get_cost_data_js, name="cost"),
]

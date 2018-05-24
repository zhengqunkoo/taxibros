from django.urls import path
from django.conf import settings
from . import views

app_name = 'visualize'
urlpatterns = [
    path('', views.index, name='index'),
    path('genTime.js', views.gen_time_js, name='genTime'),
    path('genLoc.js',views.gen_loc_js,name='genLoc'),
    path('maps.js', views.maps_js, name='map'),
]

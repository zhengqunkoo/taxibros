from django.urls import path
from django.conf import settings
from . import views

app_name = 'visualize'
urlpatterns = [
    path('', views.index, name='index'),
    path('gen.js', views.gen_js, name='gen.js'),
    path('maps.js', views.maps_js, name='js'),
]

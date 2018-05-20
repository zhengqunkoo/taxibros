from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('maps.js', views.genjs, name='js'),
]

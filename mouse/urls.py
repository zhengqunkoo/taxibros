from django.urls import path
from . import views

app_name = "mouse"
urlpatterns = [
    path("", views.index, name="index"),
    path("play.js", views.play, name="play"),
    path("get_record.js", views.get_record, name="get_record"),
    path("set_record.js", views.set_record, name="set_record"),
]

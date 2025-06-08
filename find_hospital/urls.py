# find_hospital/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.find_hospital, name='find_hospital'),
]
from django.urls import path
from .views import monitor_index

app_name = 'monitor'
urlpatterns = [
    path('', monitor_index, name="index"),
]
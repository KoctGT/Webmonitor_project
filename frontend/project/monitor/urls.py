from django.urls import path
from .views import monitor_index, ignore, solve, charts

app_name = 'monitor'
urlpatterns = [
    path('', monitor_index, name="index"),
    path('ignore/<int:id>', ignore, name='ignore'),
    path('solve/<int:id>', solve, name='solve'),
    path('charts', charts, name='charts'),
]
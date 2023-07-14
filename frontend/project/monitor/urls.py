from django.urls import path
from .views import monitor_index, ignore, solve, line_chart, chartjs

app_name = 'monitor'
urlpatterns = [
    path('', monitor_index, name="index"),
    path('ignore/<int:id>', ignore, name='ignore'),
    path('solve/<int:id>', solve, name='solve'),
    path('chartjs', chartjs, name='chartjs'),
]
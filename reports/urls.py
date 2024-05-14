from django.urls import path
from .views import *

urlpatterns = [
    path('reports_index/', index, name='reports_index'),
    path('create_report/', create_report, name='create_report'),
    path('download_report/', download_file, name='download_report'),
    path('edit_report/', edit_report, name='edit_report'),
]

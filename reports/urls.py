from django.urls import path
from .views import *

urlpatterns = [
    path('reports_index/', index, name='reports_index'),
    path('create_report/', create_report, name='create_report'),
]

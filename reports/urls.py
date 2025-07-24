from django.urls import path
from .views import *

urlpatterns = [
    path('all_reports/', all_reports, name='all_reports'),
    path('archived_reports/', archived_reports, name='all_reports'),
    path('plans_n_reports/', plans_reports_index, name='reports_index'),
    path('reports_index/', reports_index, name='reports_index'),
    path('plans_index/', plans_index, name='plans_index'),
    path('objectives_index/', objectives_index, name='objectives_index'),
    path('reports/<str:period>', get_reports, name='get_reports'),
    path('plans/<str:period>', get_plans, name='get_plans'),
    path('objectives/<str:section_name>', get_objectives, name='get_objectives'),
    path('create_report/', create_report, name='create_report'),
    path('download_report/', download_file, name='download_report'),
    path('edit_report/', edit_report, name='edit_report'),
]

from django.urls import path
from .views import *

urlpatterns = [
    path('dashboard/', dashboard_index, name='dashboard_index'),
    path('dashboard/filter/<str:item>', dashboard_filter, name='dashboard_filter'),
    path('dashboard/pbnc/upload', pbnc_upload, name='pbnc_upload'),
    path('dashboard/td/upload', td_upload, name='td_upload'),
    path('dashboard/upo/upload', upo_upload, name='upo_upload'),
    path('dashboard/inspections/upload', inspections_upload, name='inspections_upload'),
    path('dashboard/maintenance/upload', maintenance_upload, name='maintenance_upload'),
    ]

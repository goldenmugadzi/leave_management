from django.urls import path
from .views import *

urlpatterns = [
    path('overview/', dashboard_index, name='dashboard_index'),
    path('filter/<str:item>', dashboard_filter, name='dashboard_filter'),
    path('pbnc/upload', pbnc_upload, name='pbnc_upload'),
    path('td/upload', td_upload, name='td_upload'),
    path('upo/upload', upo_upload, name='upo_upload'),
    path('inspections/upload', inspections_upload, name='inspections_upload'),
    path('maintenance/upload', maintenance_upload, name='maintenance_upload'),
    path('ajax', dashboards_maintenance_ajax, name='ajax_month'),
    ]

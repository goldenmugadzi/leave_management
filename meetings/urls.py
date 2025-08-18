from django.urls import path
from . import views

urlpatterns = [
    
    path('meetings/', views.create_meeting, name='create_meeting'),
    path('meetings_datatable/', views.meetings_datatable, name='meetings_datatable'),
    path('table_meeting/', views.table_meetings, name="table_asset"),
    
]

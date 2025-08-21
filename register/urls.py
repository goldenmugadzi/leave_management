from django.urls import path
from .views import attendance_record_create

urlpatterns = [
    
    path('attendance/', attendance_record_create, name='attendance_create'),
]

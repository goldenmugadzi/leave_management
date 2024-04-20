from django.urls import path
from .views import *
app_name ='comparative_schedules'

urlpatterns = [
    path('create_schedule/', create, name='create_schedule'),
    path('add_supplier/<str:tender_id>', cs_add_supplier, name='add_supplier'),
    path('compliance/<str:tender_id>', cs_compliance_table, name="tender_compliance"),
    
    path('create_data/', get_create_data, name='get_create_data'),
]
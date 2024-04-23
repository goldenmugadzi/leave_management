from django.urls import path
from .views import *
app_name ='comparative_schedules'

urlpatterns = [
    path('schedule/<str:pr_id>', get_create_cs, name='create_schedule'),
    path('create_schedule/', create, name='create_schedule'),
    path('add_supplier/<str:tender_id>', cs_add_supplier, name='add_supplier'),
    path('compliance/<str:tender_id>', cs_compliance_table, name="tender_compliance"),
    
    path('create_data/<str:pr_id>', get_create_data, name='get_create_data'),
    path('save', save_comparative_schedule, name='save_schedule'),
    path('update', update_comparative_schedule, name='update_schedule'),
    
    path('save_bid', save_cs_bid, name='save_bid'),
    
    path('save_compliance', save_cs_compliance, name='save_compliance'),
    
    path('close_compliance', save_cs_ranking, name='save_cs_ranking'),
    
]
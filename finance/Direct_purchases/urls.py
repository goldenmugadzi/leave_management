from django.urls import path
from .views import *

app_name = 'direct_purchases'

urlpatterns = [
    path('create_directPurchase', create_direct_purchase, name='create_directPurchase'),
    path('create_supplier', create_supplier, name='create_supplier'),
    # path('add_item', add_item, name='add_item'),
    path('rfq_detail/<str:rfq_id>/', rfq_detail, name='rfq_detail'),
    path('rfqs/', view_all_rfqs, name='view_all_rfqs'),
    path('rfqs_awaiting_my_action/', rfqs_awaiting_my_action, name='rfqs_awaiting_my_action'),
]

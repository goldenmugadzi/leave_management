from django.urls import path
from .views import *

app_name = 'direct_purchases'

urlpatterns = [
    path('create_directPurchase', create_direct_purchase, name='create_directPurchase'),
    path('create_supplier', create_supplier, name='create_supplier'),
    # path('add_item', add_item, name='add_item'),
    path('direct_purchase_detail/<str:DP_id>/', Direct_Purchase_detail, name='DP_detail'),
    path('rfqs/', view_all_DPs, name='view_all_rfqs'),
    path('rfqs_awaiting_my_action/', direct_purchases_awaiting_my_action, name='rfqs_awaiting_my_action'),
]

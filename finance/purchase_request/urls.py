from django.urls import path
from .views import *
app_name ='purchase_request'

urlpatterns = [
    path('create_purchase_request/', create_purchase_request, name='create_purchase_request'),
    path('add_unit_of_measurement/', AddUOM.as_view(), name='add_unit_of_measurement'),
    path('uploaduuom/', uploaduuom, name='uploaduuom'),
    # path('quote_purchase_request/<str:purchase_request_id>/', quote_purchase_request, name='quote_purchase_request'),
    path('purchase_request_detail/<str:purchase_request_id>/', purchase_request_detail, name='purchase_request_detail'),
    path('del_file/<int:id>/', del_file, name='del_file'),
    path('purchase_requests/', view_all_purchase_requests, name='view_all_purchase_requests'),
    path('search_purchase_requests/', search_purchase_requests, name='search_purchase_requests'),
 # path('purchase_requests_awaiting_my_action/', purchase_requests_awaiting_my_action, name='purchase_requests_awaiting_my_action'),
    path('purchase_request_update/<str:purchase_request_id>/', purchase_request_update, name='purchase_request_update'),
    path('create_ace_purchase_request/<str:ace_id>/', create_ace_purchase_request, name='create_ace_purchase_request'),
]
from django.urls import path
from .views import *
app_name ='purchase_request'

urlpatterns = [
    path('bid_on_pr/<str:purchase_request_id>/', bid_on_pr, name='bid_on_pr'),
    # path('purchase_request_detail/<str:purchase_request_id>/', purchase_request_detail, name='purchase_request_detail'),
    # path('purchase_requests/', view_all_purchase_requests, name='view_all_purchase_requests'),
    # path('purchase_requests_awaiting_my_action/', purchase_requests_awaiting_my_action, name='purchase_requests_awaiting_my_action'),
    # path('create_ace_purchase_request/<str:ace_id>/', create_ace_purchase_request, name='create_ace_purchase_request'),
]
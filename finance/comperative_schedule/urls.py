from django.urls import path
from .views import *
app_name ='comperative_schedule'

urlpatterns = [
    path('bid_on_pr/<str:purchase_request_id>/', bid_on_pr, name='bid_on_pr'),
    path('comperative_schedule/<str:purchase_request_id>/', comperative_schedule, name='comperative_schedule'),
    path('order_selected/<str:purchase_request_id>/', order_selected, name='order_selected'),
    # path('purchase_requests/', view_all_purchase_requests, name='view_all_purchase_requests'),
    # path('purchase_requests_awaiting_my_action/', purchase_requests_awaiting_my_action, name='purchase_requests_awaiting_my_action'),
    # path('create_ace_purchase_request/<str:ace_id>/', create_ace_purchase_request, name='create_ace_purchase_request'),
]
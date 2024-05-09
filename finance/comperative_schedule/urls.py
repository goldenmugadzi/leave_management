from django.urls import path
from .views import *
app_name ='comperative_schedule'

urlpatterns = [
    path('bid_on_pr/<str:purchase_request_id>/', bid_on_pr, name='bid_on_pr'),
    path('comperative_schedule/<str:purchase_request_id>/', comperative_schedule, name='comperative_schedule'),
    path('orders/<str:purchase_request_id>/', orders, name='orders'),
    path('order/<str:order_id>/', order, name='order'),
   ]
from django.urls import path
from .views import *

app_name = 'pettycash'

urlpatterns = [
    path('create_pettycash/', create_pettycash, name='create_pettycash'),
    path('pettycash_detail/<str:petty_id>/', pettyCash_detail, name='pettycash_detail'),
    path('rfqs/', view_all_pettycashs, name='view_all_pettycashs'),
    path('pettycashs_awaiting_my_action/', pettycash_awaiting_my_action, name='pettycashs_awaiting_my_action'),
]

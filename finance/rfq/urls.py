from django.urls import path
from .views import *

urlpatterns = [
    path('', index, name='index'),
    path('create_rfq', create_rfq_from_ace, name='create_rfq'),
    path('approve_rfq', get_to_approve_rfq, name='approve_rfq'),
    path('reject_rfq', get_to_reject_rfq, name='reject_rfq'),
   
]

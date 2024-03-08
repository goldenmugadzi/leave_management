from django.urls import path
from . import views
from .views import create_rfq_from_ace, get_to_approve_rfq, get_to_reject_rfq, index

urlpatterns = [
    path('', index, name='index'),
    path('rfq_create', rfq_create, name='create_rfq'),
    path('create_rfq', create_rfq, name='create_rfq'),
    path('create_ace_rfq', create_rfq_from_ace, name='create_rfq'),
    path('approve_rfq', get_to_approve_rfq, name='approve_rfq'),
    path('reject_rfq', get_to_reject_rfq, name='reject_rfq'),
   
]

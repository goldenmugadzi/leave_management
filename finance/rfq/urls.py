from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('create_rfq', views.create_rfq_from_ace, name='create_rfq'),
    path('approve_rfq', views.get_to_approve_rfq, name='approve_rfq'),
    path('reject_rfq', views.get_to_reject_rfq, name='reject_rfq'),
   
]

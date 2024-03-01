from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('create_rfq', views.create_rfq_from_ace, name='create_rfq'),
   
]

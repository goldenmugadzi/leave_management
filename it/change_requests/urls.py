from django.urls import path

from . import views

urlpatterns = [
    path('create_change_request', views.create_change_request, name='create_change_request'),
    
]
from django.urls import path
from .views import *

urlpatterns = [
    # Other URL patterns
    path('create_rfq/', create_rfq, name='create_rfq'),
]
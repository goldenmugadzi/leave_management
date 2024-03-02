from django.urls import path
from .views import *
app_name='approve'
urlpatterns = [
    path('create_workflow/', create_workflow, name='create_workflow'),
    path('create_steps/', create_steps, name='create_steps'),
]

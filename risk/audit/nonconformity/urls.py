from django.urls import path
from .views import *

app_name = 'nonconformity'

urlpatterns = [
    path('create_nonconformity/', create_nonconformity, name='create_nonconformity'),
    path('inbox/', view_notifications, name='inbox'),
    path('nonconformities/', view_nonconformities, name='nonconformities'),
    path('my_nonconformities/', my_nonconformities, name='my_nonconformities'),
    path('nonconformity/<int:nonconformity_id>/', nonconformity_details, name='nonconformity'),
    path('newinfo/<int:nonconformity_id>/', additionalInfoForm, name='newinfo'),
]
from django.urls import path
from .views import *

app_name = 'nonconformity'

urlpatterns = [
    path('create_nonconformity/', create_nonconformity, name='create_nonconformity'),
    path('inbox/', view_notifications, name='inbox'),
    path('nonconformities/', view_nonconformities, name='nonconformities'),

    path('nonconformity/<int:nonconformity_id>/', nonconformity_details, name='nonconformity'),
    # path('nonconformity/<int:nonconformity_id>/resolve/', resolve_nonconformity, name='resolve_nonconformity'),
    # path('nonconformity/<int:nonconformity_id>/reject/', reject_nonconformity, name='reject_nonconformity'),
]
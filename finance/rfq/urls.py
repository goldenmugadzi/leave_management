from django.urls import path
from .views import *
app_name ='rfq'
urlpatterns = [
    # Other URL patterns
    path('create_rfq/', create_rfq, name='create_rfq'),
    path('rfq_detail/<int:rfq_id>/', rfq_detail, name='rfq_detail'),
    path('rfqs/', view_all_rfqs, name='view_all_rfqs'),
    path('rfqs_awaiting_my_action/', rfqs_awaiting_my_action, name='rfqs_awaiting_my_action'),
]
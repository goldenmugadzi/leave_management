from django.urls import path
from .views import *
app_name ='procurement'

urlpatterns = [
    path('i', CreateRFQView.as_view(), name='i'),
    # path('rfq_create', rfq_create, name='create_rfq'),
    # path('create_rfq', create_rfq, name='create_rfq'),
    # path('create_ace_rfq', create_rfq_from_ace, name='create_rfq'),
    # path('approve_rfq', get_to_approve_rfq, name='approve_rfq'),
    # path('reject_rfq', get_to_reject_rfq, name='reject_rfq'),
    path('create_rfq/', create_rfq, name='create_rfq'),
    path('create_ace_rfq/<int:ace_id>/', create_ace_rfq, name='create_ace_rfq'),
    path('rfq_detail/<str:rfq_id>/', rfq_detail, name='rfq_detail'),
    path('rfqs/', view_all_rfqs, name='view_all_rfqs'),
    path('rfqs_awaiting_my_action/', rfqs_awaiting_my_action, name='rfqs_awaiting_my_action'),
]

from django.urls import path
from .views import *
app_name ='tempertoken'

urlpatterns = [
     path('create_tempertoken/', create_tempertoken, name='create_tempertoken'),
    path('tempertoken/<str:tempertoken_id>/', tempertoken_details, name='tempertoken'),
    path('tempertokens/', view_all_tempertokens, name='tempertokens'),
    # path('tempertokens_awaiting_my_action/', tempertokens_awaiting_my_action, name='tempertokens_awaiting_my_action'),
]

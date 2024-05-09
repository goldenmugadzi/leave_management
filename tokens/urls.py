from django.urls import path
from .views import *
app_name ='tokens'

urlpatterns = [
     path('create_token/', create_token, name='create_token'),
    path('token/<str:token_id>/', token_details, name='token'),
    path('tokens/', view_all_tokens, name='tokens'),
    path('tokens_awaiting_my_action/', awaiting_my_action, name='tokens_awaiting_my_action'),
]

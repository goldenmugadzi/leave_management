from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_meter_token, name='create_meter_token'),
    path('update/<int:pk>/', views.update_meter_token, name='update_meter_token'),
    path('delete/<int:pk>/', views.delete_meter_token, name='delete_meter_token'),
    path('', views.display_meter_tokens, name='display_meter_tokens'),
]

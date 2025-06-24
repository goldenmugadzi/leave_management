from django.urls import path
from . import views

urlpatterns = [

    path('leave/', views.leave_create, name='leave_create'),
]
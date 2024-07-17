# urls.py
from django.urls import path
from . import views

app_name = 'esearch'
urlpatterns = [
    path('index_all_files/', views.index_all_files, name='index_all_files'),
]
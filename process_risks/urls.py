from django.urls import path
from . import views
urlpatterns=[
    path('',views.index,name='index'),
    path('create',views.create,name='create'),
    path('commercial',views.view_Commercial,name='commercial'),
    path('engineering',views.view_Engineering,name='engineering'),
    path('download_file', views.download_file, name='download_file'),
    path('procurement',views.view_Procurement,name='procurement'),
    path('finance',views.view_Finance,name='finance'),
    path('ict',views.view_ICT,name='ict'),
    path('hr',views.view_HR,name='hr'),
    path('risk',views.view_Risk,name='risk'),
    path('table',views.view_files,name='table'),
    path('edit_file',views.edit_file,name='edit'),
]
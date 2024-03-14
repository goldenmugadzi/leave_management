from django.urls import path
from . import views

urlpatterns =[
#  path('view-process',views.view_process, name='view-process'),

    path('process_maps/',views.view_Map, name='process_maps'),
    path('',views.index,name='index'),
    path('create/',views.create,name='create process map'),
    path('table/',views.view_process_map_table,name='process map table'),
    path('client/',views.view_Client,name='commercial client processes'),
    path('payment/',views.view_payment,name='commercial payment processes'),
    path('revenue/',views.view_revenue_assurance,name='revenue'),
    path('planning/',views.view_eng_planning,name='planning'),
    path('maintenance/',views.view_Maintenance,name='maintenance'),
    path('project/',views.view_eng_project,name='engineering project processes'),
    path('download_file/', views.download_file, name='download_file'),
    path('procurement/',views.view_Procurement,name='procurement'),
    path('finance/',views.view_Finance,name='finance'),
    path('ict/',views.view_ICT,name='ict'),
    path('hr/',views.view_HR,name='hr'),
    path('risk/',views.view_Risk,name='risk'),
    path('testadd/',views.bulk_create,name='bulk_create'),
    path('commercial/',views.view_Commercial,name='Commercial Processes'),
    path('engineering/',views.view_Engineering,name='Engineering Processes'),
    # path('edit_file',views.edit_file,name='edit'),
 ]

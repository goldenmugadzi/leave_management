from django.urls import path

from . import views

urlpatterns = [
    path('change_request_index', views.change_request_index, name='change_request_index'),
    path('create_change_request', views.create_change_request, name='create_change_request'),
    path('create_new_profile', views.create_new_profile, name='create_new_profile'),
    path('datatables/<str:view>', views.datatable_data, name='datatable_data'),
    path('new_profile_request', views.new_profile_request, name='new_profile_request'),
    path('update_new_profile_request', views.update_new_profile_request, name='update_new_profile_request'),
    path('view_change_request', views.view_profile_request, name='view_profile_request'),
    path('approve_change_request', views.approve_profile_request, name='approve_profile_request'),
    path('profile_modification/get_user_data/<str:username>', views.get_user_data, name='get_user_data'),
    path('profile_modification/create', views.profile_modification_request, name='profile_modification_request'),
    path('update_change_request', views.update_change_request, name='update_change_request'),
    path('profile_deactivation_request', views.profile_deactivation_request, name='profile_deactivation_request'),
    
]
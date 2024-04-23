from django.urls import path

from . import views

urlpatterns = [
    path('users-index', views.get_user_records, name='index_user'),
    path('user/create', views.add_user, name='user_create'),
    path('user/update', views.update_user, name='user_update'),
    path('user/groups', views.get_user_all_groups, name='get_user_all_groups'),
    path('user/delete', views.delete_user, name='user_delete'),
    path('user/reset', views.reset_user_password, name='user_reset'),
    path('user/change-password', views.change_user_password, name='change_user_password'),
    path('user/add_centers', views.add_centers, name='add_centers'),
    
    path('filtered_districts/<str:region_id>', views.get_filtered_districts, name='filtered_regions'),
    path('filtered_depots/<str:district_id>', views.get_filtered_depots, name='filtered_depots'),
    path('import', views.import_users, name='import_users'),
]
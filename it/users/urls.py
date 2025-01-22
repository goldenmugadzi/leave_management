from django.urls import path

from . import views

urlpatterns = [
    path('users-index', views.get_user_records, name='index_user'),
    path('user/create', views.add_user, name='user_create'),
    path('user/update', views.update_user, name='user_update'),
    path('user/profile', views.view_user, name='view_user'),
    path('user/groups', views.get_user_all_groups, name='get_user_all_groups'),
    path('user/reset', views.reset_user_password, name='user_reset'),
    path('user/change-password', views.change_user_password, name='change_user_password'),
    path('user/add_centers', views.add_centers, name='add_centers'),
    path('user/email', views.ms_exhange_test, name='ms_exhange_test'),
    path('user/centers', views.user_centers, name='user_centers'),
    path('user/center/parents/<str:center_code>', views.get_center_parents, name='get_center_parents'),
    
    path('filtered_districts/<str:region_id>', views.get_filtered_districts, name='filtered_regions'),
    path('filtered_centers/<str:region_id>', views.get_filtered_centers, name='get_filtered_centers'),
    path('filtered_depots/<str:district_id>', views.get_filtered_depots, name='filtered_depots'),
    path('import', views.import_users, name='import_users'),
    path('datatables', views.datatable_data, name='datatable_data'),
    path('import_old_users', views.import_old_users, name='import_old_users'),
    path('centfilter/<str:id>', views.get_center_filter, name='get_center_filter'),
    
    path('sections', views.get_sections, name='get_sections'),
    path('cost_centers', views.get_cost_centers, name='get_cost_centers'),
    path('regions', views.get_regions, name='get_regions'),

    path('setroles', views.roles_modal, name='setroles'),
    path('set_requesters', views.set_requesters, name='set_requesters'),
    path('deactivate_user', views.deactivate_user, name='deactivate_user'),
    path('activate_user', views.activate_user, name='activate_user'),
]
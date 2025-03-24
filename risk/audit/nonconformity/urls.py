from django.urls import path
from .views import *

app_name = 'nonconformity'

urlpatterns = [
    path('create_nonconformity/', create_nonconformity, name='create_nonconformity'),
    path('create_nonconformity/<str:clause>', create_nonconformity_from_checklist, name='create_nonconformity_from_checklist'),
    path('inbox/', view_notifications, name='inbox'),
    path('nonconformities/', view_nonconformities, name='nonconformities'),
    path('nonconformity_repots/', nonconformity_reports, name='nonconformity_reports'),
    path('i_created/', Icreated_nonconformities, name='i_created'),
    path('assigned_to_me/', assigned_to_me, name='assigned_to_me'),
    path('nonconformity/<str:nonconformity_id>/', nonconformity_details, name='nonconformity'),
    path('awaiting_my_action/', awaiting_my_action, name='awaiting_my_action'),
    path('create_clause/', create_clause, name='create_clause'),
    path('create_topic/<str:clause>', create_topic, name='create_topic'),
    path('create_iso_req/<str:topic>', create_iso_req, name='create_iso_req'),
    # path('del_file/<int:id>/', del_file, name='del_file'),

    path('edit_clause/<str:clause>', edit_clause, name='edit_clause'),
    path('edit_topic/<str:topic>', edit_topic, name='edit_topic'),
    path('edit_iso_req/<str:iso_req>', edit_iso_req, name='edit_iso_req'),

    path('notify/', notify, name='notify'),
    path('checklist/', checklist, name='checklist'),
    path('migrate_nc/', migrate_nonconformities, name='migrate_nc'),
    path('editable_checklist/', editable_checklist, name='editable_checklist'),
]
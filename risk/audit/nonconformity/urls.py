from django.urls import path
from .views import *

app_name = 'nonconformity'

urlpatterns = [
    path('create_nonconformity/', create_nonconformity, name='create_nonconformity'),
    path('create_nonconformity/<str:clause>', create_nonconformity_from_checklist, name='create_nonconformity_from_checklist'),
    path('inbox/', view_notifications, name='inbox'),
    path('nonconformities/', view_nonconformities, name='nonconformities'),
    path('my_nonconformities/', my_nonconformities, name='my_nonconformities'),
    path('nonconformity/<int:nonconformity_id>/', nonconformity_details, name='nonconformity'),
    
    path('create_clause/', create_clause, name='create_clause'),
    path('create_topic/<str:clause>', create_topic, name='create_topic'),
    path('create_iso_req/<str:topic>', create_iso_req, name='create_iso_req'),

    path('edit_clause/<str:clause>', edit_clause, name='edit_clause'),
    path('edit_topic/<str:topic>', edit_topic, name='edit_topic'),
    path('edit_iso_req/<str:iso_req>', edit_iso_req, name='edit_iso_req'),

    path('newinfo/<int:nonconformity_id>/', additionalInfoForm, name='newinfo'),
    path('notify/', notify, name='notify'),
    path('checklist/', checklist, name='checklist'),
    path('editable_checklist/', editable_checklist, name='editable_checklist'),
]
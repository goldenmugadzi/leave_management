from django.urls import path
from . import views

app_name = 'process_management'

urlpatterns = [
    # Process list view - displays departmental sections
    path('', views.process_list_view, name='process_list'),
    # Department processes view - displays processes within a department
    path('department/<int:department_id>/', views.process_department_view, name='department_processes'),
    # Process detail view - displays individual process with all components
    path('detail/<int:process_id>/', views.process_detail_view, name='process_detail'),
    
    # Document download views
    path('document/download/<int:document_id>/', views.document_download_view, name='document_download'),
    path('process/<int:process_id>/document/<str:document_type>/download/', 
         views.document_download_by_process_and_type, name='document_download_by_type'),
    
    # Document upload views
    path('process/<int:process_id>/upload/', views.document_upload_view, name='document_upload'),
    path('document/<int:document_id>/replace/', views.document_replace_view, name='document_replace'),
    
    # Process management views
    path('create/', views.process_create_view, name='process_create'),
    path('edit/<int:process_id>/', views.process_edit_view, name='process_edit'),
    path('delete/<int:process_id>/', views.process_delete_view, name='process_delete'),
    
    # IMS-specific views
    path('ims/import/', views.ims_import_view, name='ims_import'),
    path('ims/processes/', views.ims_processes_view, name='ims_processes'),
    path('ims/process/<int:process_id>/', views.ims_process_detail_view, name='ims_process_detail'),
]
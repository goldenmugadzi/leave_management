from django.urls import path
from . import views

app_name = 'comm_files'

urlpatterns = [
    # Customer URLs
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/create/', views.create_customer, name='create_customer'),
    path('customers/import/', views.import_customers_excel, name='import_customers_excel'),
    path('customers/import/sample/', views.download_sample_excel, name='download_sample_excel'),
    path('customers/<str:customer_id>/', views.customer_detail, name='customer_detail'),
    path('customers/<str:customer_id>/edit/', views.edit_customer, name='edit_customer'),
    
    # Document URLs
    path('customers/<str:customer_id>/upload-document/', views.document_upload, name='document_upload'),
    path('documents/review/<int:document_id>/', views.document_review, name='document_review'),
    
    # Document Type Management URLs
    path('document-types/', views.document_type_list, name='document_type_list'),
    path('document-types/create/', views.document_type_create, name='document_type_create'),
    path('document-types/<int:doc_type_id>/edit/', views.document_type_edit, name='document_type_edit'),
    path('document-types/<int:doc_type_id>/delete/', views.document_type_delete, name='document_type_delete'),
    
    # Onboarding Process URLs
    path('customers/<str:customer_id>/start-onboarding/', views.start_onboarding, name='start_onboarding'),
    path('onboarding-process/<int:process_id>/update-status/', views.update_onboarding_status, name='update_onboarding_status'),
]
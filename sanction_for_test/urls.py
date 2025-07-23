from django.urls import path
from . import views

app_name = 'sanction_for_test'

urlpatterns = [
    # List view
    path('', views.sanction_list, name='list'),
    
    # Create new form
    path('create/', views.create_sanction_form, name='create'),
    
    # Detail view
    path('<int:pk>/', views.detail_sanction_form, name='detail'),
    
    # Edit form
    path('<int:pk>/edit/', views.edit_sanction_form, name='edit'),
    
    # Delete form
    path('<int:pk>/delete/', views.delete_sanction_form, name='delete'),
    
    # Quick actions
    path('<int:pk>/action/', views.quick_action, name='quick_action'),
    
    # AJAX endpoints
    path('<int:pk>/status/', views.ajax_form_status, name='ajax_status'),
]

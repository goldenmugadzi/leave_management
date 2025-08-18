from django.urls import path
from . import views

app_name = 'sanction_for_test'

urlpatterns = [
    # List view
    path('', views.list_view, name='list'),
    
    # Create new form
    path('create/', views.create_view, name='create'),
    
    # Detail view
    path('<int:pk>/', views.detail_view, name='detail'),
    
    # Edit form
    path('<int:pk>/edit/', views.edit_view, name='edit'),
    
    # Delete form
    path('<int:pk>/delete/', views.delete_view, name='delete'),
    
    # Status update
    path('<int:pk>/status/', views.update_status, name='update_status'),
    
    # Add comment
    path('<int:pk>/comment/', views.add_comment, name='add_comment'),
    
    # Add attachment
    path('<int:pk>/attachment/', views.add_attachment, name='add_attachment'),
    
    # Approval action
    path('<int:pk>/approve/', views.approve_action, name='approve_action'),
    
    # Reports
    path('reports/', views.reports_view, name='reports'),
]

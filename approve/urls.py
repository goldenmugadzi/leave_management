from django.urls import path
from .views import *
app_name='approve'
urlpatterns = [
    path('create_workflow/', WorkflowCreateView.as_view(), name='create_workflow'),
    path('workflow/<int:workflow_id>/add-steps/', step_formset_view, name='add_steps'),
    path('workflow/<int:pk>/', WorkflowDetailView.as_view(), name='workflow_detail'),
    path('approve/<int:process_id>/', approve_step, name='approve'), 
]
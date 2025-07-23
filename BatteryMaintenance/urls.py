from django.urls import path
from .views import *
app_name='approve'
urlpatterns = [
    path('install_battery/', InstallBattery.as_view(), name='install_battery'),
    # path('workflow/<int:workflow_id>/add-steps/', step_formset_view, name='add_steps'),
    # path('workflow/<int:pk>/', WorkflowDetailView.as_view(), name='workflow_detail'),
    # path('approve/<int:process_id>/', approve_step, name='approve'), 
    ]

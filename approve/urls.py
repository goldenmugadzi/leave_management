from django.urls import path
from .views import *
app_name='approve'
urlpatterns = [
    path('create_workflow/', create_workflow, name='create_workflow'),
    path('create_steps/', create_steps, name='create_steps'),

    # path('create_workflow/', WorkflowCreateView.as_view(), name='create_workflow'),
    # path('edit_workflow/<int:pk>/', WorkflowUpdateView.as_view(), name='edit_workflow'),
]

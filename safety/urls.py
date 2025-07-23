from django.urls import path
from .views import ControllersInstructionFormCreateView, ControllersInstructionFormListView

urlpatterns = [
    path('new-instruction-form/', ControllersInstructionFormCreateView.as_view(), name='new-instruction-form'),
    path('instruction-form-list/', ControllersInstructionFormListView.as_view(), name='instruction-form-list'),
]
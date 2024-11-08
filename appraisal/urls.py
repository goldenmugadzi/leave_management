from django.urls import path
from .view import AppraisalCreateView

urlpatterns = [
    path('create/', AppraisalCreateView.as_view(), name='create_appraisal'),

    ]
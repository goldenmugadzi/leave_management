from django.urls import path
from .views import *

app_name = 'pretask_risk_assessment'

urlpatterns = [
    path('pretask_risk_assessments', PretaskRiskAssessmentListView.as_view(), name='list'),
    path('jobs', JobListView.as_view(), name='jobs'),
    path('job/<int:pk>/',JobDetailView.as_view(),name='job'),
    path('pretask_risk_assessment/<int:pk>/', PretaskRiskAssessmentDetailView.as_view(), name='detail_pretask_risk_assessment'),
    path('create_pretask_risk_assessment/', PretaskRiskAssessmentCreateView.as_view(), name='create_pretask_risk_assessment'),
    path('job_create/', JobCreateView.as_view(), name='job_create'),
]

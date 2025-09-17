from django.urls import path
from .views import (
    PretaskRiskAssessmentListView,
    PretaskRiskAssessmentDetailView,
    PretaskRiskAssessmentCreateView,
)

app_name = 'pretask_risk_assessment'

urlpatterns = [
    path('', PretaskRiskAssessmentListView.as_view(), name='list'),
    path('<int:pk>/', PretaskRiskAssessmentDetailView.as_view(), name='detail'),
    path('create/', PretaskRiskAssessmentCreateView.as_view(), name='create'),
]

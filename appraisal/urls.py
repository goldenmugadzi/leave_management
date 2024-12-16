from django.urls import path
from .view import (AppraisalCreateView, 
                   ExperienceCreateView, 
                   AppraisalTemplateView, 
                   experience_list_api,
                   PerformancePlanAndAssessmentAppraisalTemplateView,
                   PerformancePlanAndAssessmentTemplateView,
                   PerformanceReviewsApprovalView,
                   TrainingAndDevelopmentUpdateView,
                   KRATemplateView, 
                   KRACreateView
                   )

urlpatterns = [
    path('', AppraisalTemplateView.as_view(), name='appraisal_index'),
    path('create/', AppraisalCreateView.as_view(), name='create_appraisal'),

    # ================= Experience urls ============================
    path('experience/create/', ExperienceCreateView.as_view(), name='create_experience'),
    
    # ================= Performance urls =================================
    path('performance', PerformancePlanAndAssessmentAppraisalTemplateView.as_view(), name='performance_review_index'),
    path('performance/<int:appraisal_id>', PerformancePlanAndAssessmentTemplateView.as_view(), name='performance_review_detail'),
    path('performance/review/<int:appraisal_id>/<int:quarter>', PerformanceReviewsApprovalView.as_view(), name='performance_review_create'),
    path('performance/training-development/<int:appraisal_id>/<int:quarter>', TrainingAndDevelopmentUpdateView.as_view(), name='training_development_update'),
    
    # ================== KRA urls =================================
    path('kra', KRATemplateView.as_view(), name='kra_index'),
    path('kra/new', KRACreateView.as_view(), name='kra_create'),
    
    # ----- api ------
    path('api/experience-list/', experience_list_api, name='experience_list_api'),
    ]
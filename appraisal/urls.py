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
                   KRACreateView,
                   KRAUpdateView,
                   KraActivityIndexTemplateView,
                   KraActivityCreateView,
                   KraActivityUpdateView,
                   TargetsIndexView,
                   TargetCreateView,
                   TargetUpdateView
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
    path('kra/<int:pk>', KRAUpdateView.as_view(), name='kra_update'),
    path('kra/<int:kra_id>/activity', KraActivityIndexTemplateView.as_view(), name='kra_activity_index'),
    path('kra/<int:kra_id>/activity/new', KraActivityCreateView.as_view(), name='kra_activity_create'),
    path('kra/<int:kra_id>/activity/<int:activity_id>', KraActivityUpdateView.as_view(), name='kra_activity_update'),
    path('kra/activity/<int:activity_id>/targets', TargetsIndexView.as_view(), name='target_index'),
    path('kra/activity/<int:activity_id>/targets/new', TargetCreateView.as_view(), name='target_create'),
    path('kra/activity/<int:activity_id>/targets/<int:target_id>', TargetUpdateView.as_view(), name='target_update'),
    
    # ----- api ------
    path('api/experience-list/', experience_list_api, name='experience_list_api'),
    ]
from django.urls import path
from .view import (AppraisalCreateView,
                   AppraisalUpdateView,
                   ExperienceCreateView,
                   AppraisalExperienceCreateView,
                   AppraisalExperienceUpdateView,
                   approveAppraisal,
                   ExperienceListView,
                   AppraisalTemplateView,
                   experience_list_api,
                   kra_list_api,
                   PerformancePlanAndAssessmentAppraisalTemplateView,
                   PerformancePlanAndAssessmentTemplateView,
                   PerformanceReviewsApprovalView,
                   TrainingAndDevelopmentUpdateView,
                   KRATemplateView,
                   KRACreateView,
                   KRAUpdateView,
                   KRADetailView,
                   KraActivityIndexTemplateView,
                   KraActivityCreateView,
                   KraActivityUpdateView,
                   TargetScoreUpdateView,
                   UserQualificationTemplateView,
                   UserQualificationCreateView,
                   UserQualificationUpdateView,
                   AppraisalKraCreateView,
                   AppraisalKraTemplateView,
                   AppraisalKraUpdateView
                   )

urlpatterns = [
    path('', AppraisalTemplateView.as_view(), name='appraisal_index'),
    path('create/', AppraisalCreateView.as_view(), name='create_appraisal'),
    path('update/<int:pk>', AppraisalUpdateView.as_view(), name='update_appraisal'),
    path('approval/<int:appraisal_id>', approveAppraisal, name='appraisal_approval'),

    # ================= Experience urls ============================
    path('experience/create/', ExperienceCreateView.as_view(), name='create_experience'),
    path('experience/<int:appraisal_id>/', ExperienceListView.as_view(), name='list_experience'),
    path('appraisal-experience/<int:appraisal_id>/', AppraisalExperienceCreateView.as_view(), name='appraisal_experience_create'),
    path('appraisal-experience/<int:appraisal_exp_id>/view', AppraisalExperienceUpdateView.as_view(), name='appraisal_experience_update'),
    
    # ================= Performance urls =================================
    path('performance', PerformancePlanAndAssessmentAppraisalTemplateView.as_view(), name='performance_review_index'),
    path('performance/<int:appraisal_id>', PerformancePlanAndAssessmentTemplateView.as_view(), name='performance_review_detail'),
    path('performance/review/<int:appraisal_id>/<int:year>/<int:quarter>', PerformanceReviewsApprovalView.as_view(), name='performance_review_create'),
    path('performance/training-development/<int:appraisal_id>/<int:year>/<int:quarter>', TrainingAndDevelopmentUpdateView.as_view(), name='training_development_update'),
    
    # ========================Qualification View=========================
    path('qualification/<int:user_id>/', UserQualificationTemplateView.as_view(), name='list_qualification'),
    path('qualification/<int:appraisal_id>', UserQualificationCreateView.as_view(), name='create_qualification'),
    path('qualification/<int:qualification_id>/view', UserQualificationUpdateView.as_view(), name='update_qualification'),
    
    
    # ================== KRA urls =================================
    path('kra/<int:appraisal_id>/new', KRACreateView.as_view(), name='kra_create'),
    path('kra/<int:appraisal_id>/list', KRATemplateView.as_view(), name='kra_index'),
    path('kra/detail/<int:appraisal_id>', KRADetailView.as_view(), name='kra_detail'),
    path('kra/activity/<int:activity_id>/targets/<int:target_id>/score', TargetScoreUpdateView.as_view(), name='score'),
    
    path('kra/<int:appraisal_id>/appraisal-kra', AppraisalKraTemplateView.as_view(), name='appraisal_kra_index'),
    path('kra/<int:appraisal_id>/appraisal-kra/new', AppraisalKraCreateView.as_view(), name='appraisal_kra_create'),
    path('kra/appraisal-kra/<int:appraisal_kra_id>', AppraisalKraUpdateView.as_view(), name='appraisal_kra_update'),
    
    path('kra/<int:appraisal_kra_id>/activity', KraActivityIndexTemplateView.as_view(), name='kra_activity_index'),
    path('kra/<int:appraisal_kra_id>/activity/new', KraActivityCreateView.as_view(), name='kra_activity_create'),
    path('kra/activity/<int:activity_id>', KraActivityUpdateView.as_view(), name='kra_activity_update'),
    
    
    # ----- api ------
    path('api/experience-list/', experience_list_api, name='experience_list_api'),
    path('api/kra-list/<int:appraisal_id>', kra_list_api, name='kra_list_api'),
    ]
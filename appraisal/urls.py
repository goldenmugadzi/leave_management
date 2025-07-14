from django.urls import path
from .view import (AppraisalCreateView,
                   AppraisalUpdateView,
                   ExperienceCreateView,
                   AppraisalExperienceCreateView,
                   AppraisalExperienceUpdateView,
                   ExperienceListView,
                   AppraisalTemplateView,
                   experience_list_api,
                   kra_list_api,
                   internal_server_error_view,
                   PerformancePlanAndAssessmentAppraisalTemplateView,
                   PerformancePlanAndAssessmentTemplateView,
                   PerformanceReviewsApprovalView,
                   TrainingAndDevelopmentUpdateView,
                   TrainingAndDevelopmentTemplateView,
                   KRATemplateView,
                   KRACreateView,
                   KRAUpdateDetailView,
                   KRAOutComeTemplateView,
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
                   AppraisalKraUpdateView,
                   AppraisalKraDetailView,
                   AppraisalKraReviewerStatusUpdateView,
                   PerformanceDimensionTemplateView,
                   PerformanceDimensionTemplateCreateView,
                   PerformanceDimensionTemplateUpdateView,
                   ScoreDocumentCreateView,
                   ScoreDocumentUpdateView,
                   target_score_supporting_docs_view,
                   DepartmentObjectiveTemplateView,
                   DepartmentObjectiveCreateView,
                   DepartmentObjectiveDetailUpdateView
                   )

urlpatterns = [
    path('', AppraisalTemplateView.as_view(), name='appraisal_index'),
    path('create/', AppraisalCreateView.as_view(), name='create_appraisal'),
    path('update/<int:pk>', AppraisalUpdateView.as_view(), name='update_appraisal'),
    path('server-error/', internal_server_error_view, name='server_error_view'),

    # ================= Experience urls ============================
    path('experience/create/', ExperienceCreateView.as_view(), name='create_experience'),
    path('experience/<int:appraisal_id>/', ExperienceListView.as_view(), name='list_experience'),
    path('appraisal-experience/<int:appraisal_id>/', AppraisalExperienceCreateView.as_view(), name='appraisal_experience_create'),
    path('appraisal-experience/<int:appraisal_exp_id>/view', AppraisalExperienceUpdateView.as_view(), name='appraisal_experience_update'),
    
    # ================= Performance urls =================================
    path('performance', PerformancePlanAndAssessmentAppraisalTemplateView.as_view(), name='performance_review_index'),
    path('performance/<int:appraisal_id>/performance-progress-review', PerformancePlanAndAssessmentTemplateView.as_view(), name='performance_review_detail'),
    path('performance/review/<int:appraisal_id>/<int:year>/<int:quarter>', PerformanceReviewsApprovalView.as_view(), name='performance_review_create'),
    path('performance/<int:appraisal_id>/training-development', TrainingAndDevelopmentTemplateView.as_view(), name='training_development_index'),
    path('performance/training-development/<int:appraisal_id>/<int:year>/<int:quarter>', TrainingAndDevelopmentUpdateView.as_view(), name='training_development_update'),
    
    # ========================Qualification View=========================
    path('qualification/<int:user_id>/', UserQualificationTemplateView.as_view(), name='list_qualification'),
    path('qualification/<int:appraisal_id>', UserQualificationCreateView.as_view(), name='create_qualification'),
    path('qualification/<int:qualification_id>/view', UserQualificationUpdateView.as_view(), name='update_qualification'),
    
    # ======================== Departmental workplan =========================
    path('departmental-workplan/list', DepartmentObjectiveTemplateView.as_view(), name='departmental_workplan_index'),
    path('departmental-workplan/create', DepartmentObjectiveCreateView.as_view(), name='departmental_objective_create'),
    path('departmental-workplan/<int:departmental_objective_id>', DepartmentObjectiveDetailUpdateView.as_view(), name='departmental_workplan_update_detail'),
    
    
    # ================== KRA urls =================================
    path('kra/list', KRATemplateView.as_view(), name='kra_index'),
    path('kra/new', KRACreateView.as_view(), name='kra_create'),
    path('kra/<int:kra_id>', KRAUpdateDetailView.as_view(), name='kra_update_detail'),
    path('kra/outcomes/<int:kra_id>', KRAOutComeTemplateView.as_view(), name='kra_outcomes_index'),
    
    path('kra/<int:appraisal_id>/appraisal-kra', AppraisalKraTemplateView.as_view(), name='appraisal_kra_index'),
    path('kra/<int:appraisal_id>/appraisal-kra/new', AppraisalKraCreateView.as_view(), name='appraisal_kra_create'),
    path('kra/appraisal-kra/<int:appraisal_kra_id>', AppraisalKraUpdateView.as_view(), name='appraisal_kra_update'),
    path('kra/appraisal-kra/detail/<int:appraisal_kra_id>', AppraisalKraDetailView.as_view(), name='appraisal_kra_detail'),
    
    
    path('kra/<int:appraisal_kra_id>/activity', KraActivityIndexTemplateView.as_view(), name='kra_activity_index'),
    path('kra/<int:appraisal_kra_id>/activity/new', KraActivityCreateView.as_view(), name='kra_activity_create'),
    path('kra/activity/<int:activity_id>', KraActivityUpdateView.as_view(), name='kra_activity_update'),
    
    path('kra/activity/<int:activity_id>/performance-dimension', PerformanceDimensionTemplateView.as_view(), name='performance_dimension_index'),
    path('kra/activity/<int:activity_id>/performance-dimension/new', PerformanceDimensionTemplateCreateView.as_view(), name='performance_dimension_create'),
    path('kra/activity/<int:activity_id>/performance-dimension/<int:performance_dimension_id>', PerformanceDimensionTemplateUpdateView.as_view(), name='performance_dimension_update'),
    path('kra/activity/performance-dimension/<int:performance_dimension_id>/score', TargetScoreUpdateView.as_view(), name='score_view'),
    
    path('kra/activity/performance-dimension/<int:performance_dimension_id>/scoring/<int:target_score_id>/docs/new', ScoreDocumentCreateView.as_view(), name='score_doc_create'),
    path('kra/performance-dimension/<int:performance_dimension_id>/scoring/<int:target_score_id>/docs/<int:score_doc_id>/view', ScoreDocumentUpdateView.as_view(), name='score_doc_update'),

    # ========================= Reviewer status =======================
    path('kra/reviewer-status/<int:appraisal_kra_id>', AppraisalKraReviewerStatusUpdateView.as_view(), name='appraisal_kra_reviewer_status_update'),
    
    
    # ----- api ------
    path('api/experience-list/', experience_list_api, name='experience_list_api'),
    path('api/kra-list/<int:appraisal_id>', kra_list_api, name='kra_list_api'),
    path('api/score/supporting-documents/<int:performance_dimension_pk>', target_score_supporting_docs_view, name='score_supporting_docs_view'),
    
    ]
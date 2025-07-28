from django.urls import path
from .view import (
    AppraisalCreateView,
    AppraisalUpdateView,
    ExperienceCreateView,
    AppraisalExperienceCreateView,
    AppraisalExperienceUpdateView,
    ExperienceListView,
    AppraisalTemplateView,
    experience_list_api,
    kra_list_api,
    internal_server_error_view,
    object_not_found_error_view,
    PerformancePlanAndAssessmentAppraisalTemplateView,
    PerformancePlanAndAssessmentTemplateView,
    PerformanceReviewsApprovalView,
    TrainingAndDevelopmentUpdateView,
    TrainingAndDevelopmentTemplateView,
    DepartmentObjectiveTemplateView,
    DepartmentObjectiveCreateView,
    DepartmentObjectiveDetailUpdateView,
    DepartmentOutputTemplateView,
    DepartmentOutputCreateView,
    DepartmentOutputDetailUpdateView,
    OutPutPerformanceDimensionTemplateView,
    OutPutPerformanceDimensionDetailUpdateView, 
    QualificationExperienceTemplateView,
    QualificationCreateView,
    QualificationUpdateView,
    UserExperienceCreateView,
    UserExperienceUpdateView,
    KRATemplateView,
    KRACreateView,
    KRAOutComeTemplateView,
    KRAUpdateDetailView,
    AppraisalDepartmentOutputTemplateView,
    AppraisalDepartmentPerformanceDimensionTemplateView
)

urlpatterns = [
    # ============== Appraisal ================
    path('', AppraisalTemplateView.as_view(), name='appraisal_index'),
    path('create/', AppraisalCreateView.as_view(), name='create_appraisal'),
    path('update/<int:appraisal_id>', AppraisalUpdateView.as_view(), name='update_appraisal'),
    
    # ============= errors urls ==============================
    path('server-error/', internal_server_error_view, name='server_error_view'),
    path('<slug:object_name>/not-found-error', object_not_found_error_view, name='object_not_found_error'),
    
    # ===================== KRA ==================================
    path('kra/list', KRATemplateView.as_view(), name='kra_index'),
    path('kra/new', KRACreateView.as_view(), name='kra_create'),
    path('kra/<int:kra_id>', KRAUpdateDetailView.as_view(), name='kra_update_detail'),
    path('kra/outcomes/<int:kra_id>', KRAOutComeTemplateView.as_view(), name='kra_outcomes_index'),
    
    # ================= Qualification Experience url ===================
    path('qualification-experience/user/<int:user_id>', QualificationExperienceTemplateView.as_view(), name='qualification_experience_index'),
    
    path('qualification/user/<int:user_id>', QualificationCreateView.as_view(), name='qualification_create'),
    path('qualification/<int:qualification_id>', QualificationUpdateView.as_view(), name='qualification_update'),
    
    path('experience/user/<int:user_id>', UserExperienceCreateView.as_view(), name='experience_create'),
    path('experience/<int:experience_id>', UserExperienceUpdateView.as_view(), name='user_experience_update'),
    
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
    

    # ======================== Departmental objective workplan =========================
    path('departmental-workplan/list', DepartmentObjectiveTemplateView.as_view(), name='departmental_workplan_index'),
    path('departmental-workplan/create', DepartmentObjectiveCreateView.as_view(), name='departmental_objective_create'),
    path('departmental-workplan/<int:departmental_objective_id>', DepartmentObjectiveDetailUpdateView.as_view(), name='departmental_workplan_update_detail'),
    
    # ======================== Department outputs =================================
    path('departmental-outputs/<int:departmental_objective_id>/list', DepartmentOutputTemplateView.as_view(), name='departmental_output_index'),
    path('departmental-outputs/<int:departmental_objective_id>/designation/<int:designation_id>/create', DepartmentOutputCreateView.as_view(), name='departmental_output_create'),
    path('departmental-outputs/designation/<int:designation_id>/output/<int:department_output_id>', DepartmentOutputDetailUpdateView.as_view(), name='departmental_output_detail_update'),
    
    # ========================== Output Performance Dimension ===========================
    path('departmental-output/<int:department_output_id>/performance-dimension', OutPutPerformanceDimensionTemplateView.as_view(), name='output_perf_dimension_index'),
    path('departmental-output/performance-dimension/<int:output_performance_dimension_id>', OutPutPerformanceDimensionDetailUpdateView.as_view(), name='output_perf_dimension_detail_update'),
    
    # ========================= Performance Plan Assessment ====================
    path('appraisal-department-output/<int:appraisal_id>', AppraisalDepartmentOutputTemplateView.as_view(), name="appraisal_dept_output_index"),
    path('appraisal-department-performance/<int:appraisal_department_output_id>/', AppraisalDepartmentPerformanceDimensionTemplateView.as_view(), name="appraisal_dept_perf_index"),
    
    
    # ----- api ------
    path('api/experience-list/', experience_list_api, name='experience_list_api'),
    path('api/kra-list/<int:appraisal_id>', kra_list_api, name='kra_list_api'),
    
    ]
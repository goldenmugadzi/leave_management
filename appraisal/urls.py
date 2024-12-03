from django.urls import path
from .view import (AppraisalCreateView, 
                   ExperienceCreateView, 
                   AppraisalTemplateView, 
                   experience_list_api,
                   PerformanceReviewsTemplateView,
                   PerformanceReviewsApprovalView
                   )

urlpatterns = [
    path('', AppraisalTemplateView.as_view(), name='appraisal_index'),
    path('create/', AppraisalCreateView.as_view(), name='create_appraisal'),

    # ================= Experience urls ============================
    path('experience/create/', ExperienceCreateView.as_view(), name='create_experience'),
    
    # ================= Performance urls =================================
    path('performance/review/', PerformanceReviewsTemplateView.as_view(), name='performance_review_index'),
    path('performance/review/<int:appraisal_id>/<int:quarter>', PerformanceReviewsApprovalView.as_view(), name='performance_review_detail'),
    
    # ----- api ------
    path('api/experience-list/', experience_list_api, name='experience_list_api'),
    ]
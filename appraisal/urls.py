from django.urls import path
from .view import AppraisalCreateView, ExperienceCreateView, experience_list_api

urlpatterns = [
    path('create/', AppraisalCreateView.as_view(), name='create_appraisal'),

    # ================= Experience urls ============================
    path('experience/create/', ExperienceCreateView.as_view(), name='create_experience'),
    # ----- api ------
    path('api/experience-list/', experience_list_api, name='experience_list_api'),
    ]
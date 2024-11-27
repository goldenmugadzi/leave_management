from typing import Any, Dict
from django.forms import BaseModelForm
from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic.edit import CreateView
from django.views.generic import TemplateView
from django.urls import reverse

from ..models import Appraisal, AppraisalExperience
from it.users.models import UserQualification
from ..forms import AppraisalForm, UserQualificationForm, CostCenterForm, UserProfileForm, DesignationForm, AppraisalExperienceFormset, UserQualificationFormset
from ..helpers.types import AppraisalPayloadType
from ..repository import UserQualificationRepository, AppraisalExperienceRepository, ExperienceRepository, AppraisalRepository
from ..services import AppraisalService

class AppraisalCreateView(CreateView):
    model = Appraisal
    form_class = AppraisalForm
    template_name = 'appraisal/create.html'
        
    def get_initial_forms(self, user_object)->Dict[str,Any]:
        """Helper method to initialize related forms with initial data."""
        qualification_initial_object = UserQualificationFormset(self.request.POST or None, 
            queryset=UserQualification.objects.none(),
            prefix="qualification")
        appraisal_experience_initial_object = AppraisalExperienceFormset(self.request.POST or None, queryset=AppraisalExperience.objects.none())
        return {
            'qualification_forms': qualification_initial_object,
            'appraisal_experience_forms': appraisal_experience_initial_object
        }
    
    def get_initial_user_data(self, user_object)->Dict[str, any]:
        """Helper method to set user data"""
        return {
            "user": user_object,
            "qualifications": UserQualification.objects.filter(user=user_object)
        }
    
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context =  super().get_context_data(**kwargs)
        user_object = self.request.user
        context.update(self.get_initial_forms(user_object=user_object))
        context.update(self.get_initial_user_data(user_object=user_object))
        return context
    
    def build_payload(self) -> AppraisalPayloadType:
        """Builds a structured payload dictionary grouping data by form name."""
        payload = self.request.POST
        files = self.request.FILES
        
        qualifications = [
            {
                "name": payload.get(f"qualification-{i}-name"),
                "file": files.get(f"qualification-{i}-file")  # Extract file from request.FILES
            }
            for i in range(int(payload.get("qualification-TOTAL_FORMS", 0)))
            if payload.get(f"qualification-{i}-name")
        ]
        experiences = [
            {
                "name": payload.get(f"appraisal-{i}-experience"),
                "years_of_experience": payload.get(f"appraisal-{i}-years_of_experience"),
                "months_of_experience": payload.get(f"appraisal-{i}-months_of_experience")
            }
            for i in range(int(payload.get(f"appraisal-TOTAL_FORMS", 0)))
            if payload.get(f"appraisal-{i}-experience")
        ]
        data = AppraisalPayloadType(experiences=experiences, qualifications=qualifications)
        return data
    
    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        user_object = self.request.user
        appraisal_service_handler = AppraisalService(
            appraisal_experience_repository=AppraisalExperienceRepository(),
            qualification_repository=UserQualificationRepository(),
            experience_repository=ExperienceRepository(),
            appraisal_repository=AppraisalRepository()
        )
        structured_payload = self.build_payload()
        appraisal_object = appraisal_service_handler.create_use_case(user_object=user_object, data=structured_payload)
        form.instance = appraisal_object
        
        form.instance.user = user_object
        # if len(structured_payload.experiences) == 0:
        #     # return an error 
        # print("=========>>> Structured Payload:", structured_payload)
        # input()
        return super().form_valid(form)
    
    def get_success_url(self) -> str:
        return reverse('appraisal_index')
    

class AppraisalTemplateView(TemplateView):
    template_name = 'appraisal/index.html'
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context =  super().get_context_data(**kwargs)
        appraisal_service_handler = AppraisalService(
            appraisal_experience_repository=AppraisalExperienceRepository(),
            qualification_repository=UserQualificationRepository(),
            experience_repository=ExperienceRepository(),
            appraisal_repository=AppraisalRepository()
        )
        context["appraisals"] = appraisal_service_handler.get_all_use_case(user_object=self.request.user)
        
        return context
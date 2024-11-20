from typing import Any, Dict
from django.forms import BaseModelForm
from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic.edit import CreateView
from ..models import Appraisal, AppraisalExperience
from it.users.models import UserQualification
from ..forms import AppraisalForm, UserQualificationForm, CostCenterForm, UserProfileForm, DesignationForm, AppraisalExperienceFormset, UserQualificationFormset
from django.forms.models import model_to_dict

class AppraisalCreateView(CreateView):
    model = Appraisal
    form_class = AppraisalForm
    template_name = 'appraisal/create.html'
    
    def get_initial_forms(self, user_object)->Dict[str,Any]:
        """Helper method to initialize related forms with initial data."""
        qualification_initial_object = UserQualificationFormset(self.request.POST or None, 
            queryset=UserQualification.objects.none(),
            prefix="qualification")
        designation_initial_object = user_object.designation
        cost_center_initial_object = {"name": user_object.cost_center.id}
        appraisal_experience_initial_object = AppraisalExperienceFormset(self.request.POST or None, queryset=AppraisalExperience.objects.none())

        return {
            'qualification_forms': qualification_initial_object,
            'designation_form': DesignationForm(self.request.POST or None, initial=model_to_dict(designation_initial_object)),
            'cost_center_form': CostCenterForm(self.request.POST or None, initial=cost_center_initial_object),
            'user_profile_form': UserProfileForm(self.request.POST or None, initial=model_to_dict(user_object)),
            'appraisal_experience_forms': appraisal_experience_initial_object
        }
    
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context =  super().get_context_data(**kwargs)
        user_object = self.request.user
        context.update(self.get_initial_forms(user_object=user_object))
        
        return context
    
    def build_payload(self) -> Dict[str, Any]:
        """Builds a structured payload dictionary grouping data by form name."""
        payload = self.request.POST
        data = {
            "user_profile": {
                "username": payload.get("username"),
                "designation": payload.get("designation"),
                "cost_center": payload.get("cost_center"),
                "grade": payload.get("grade"),
                "national_id": payload.get("national_id"),
            },
            "designation": {
                "identifier": payload.get("identifier"),
                "chk": payload.get("chk")
            },
            "cost_center": {
                "name": payload.get("cost_center")
            },
            "qualification_forms": [
                {
                    "name": payload.get(f"qualification-{i}-name"),
                    "file": payload.get(f"qualification-{i}-file")
                }
                for i in range(int(payload.get("qualification-TOTAL_FORMS", 0)))
            ],
            "appraisal_experience_forms": [
                {
                    "experience": payload.get(f"appraisal-{i}-experience"),
                    "years_of_experience": payload.get(f"appraisal-{i}-years_of_experience"),
                    "months_of_experience": payload.get(f"appraisal-{i}-months_of_experience")
                }
                for i in range(int(payload.get("appraisal-TOTAL_FORMS", 0)))
            ],
        }
        return data
    
    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        form.instance.user = self.request.user
        structured_payload = self.build_payload()
        print("=========>>> Structured Payload:", structured_payload)
        print("=========>>> File:", structured_payload["qualification_forms"][0]["file"])
        input()
        return super().form_valid(form)

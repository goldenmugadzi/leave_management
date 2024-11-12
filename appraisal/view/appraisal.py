from typing import Any, Dict
from django.forms import BaseModelForm
from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic.edit import CreateView
from it.users.models import UserQualification
from ..models import Appraisal, AppraisalExperience, Experience
from ..forms import AppraisalForm, UserQualificationForm, CostCenterForm, UserProfileForm, DesignationForm, AppraisalExperienceFormset
from django.forms.models import model_to_dict

class AppraisalCreateView(CreateView):
    model = Appraisal
    form_class = AppraisalForm
    template_name = 'appraisal/create.html'
    
    def get_initial_forms(self, user_object)->Dict[str,Any]:
        """Helper method to initialize related forms with initial data."""
        qualification_initial_object = UserQualification.objects.get(user=user_object)
        designation_initial_object = user_object.designation
        cost_center_initial_object = {"name": user_object.cost_center.id}
        appraisal_experience_initial_object = AppraisalExperienceFormset(self.request.POST or None, queryset=AppraisalExperience.objects.none())

        return {
            'qualification_form': UserQualificationForm(self.request.POST or None, initial=model_to_dict(qualification_initial_object)),
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
    
    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        form.instance.user = self.request.user
        print("====================>>>>>> valid", self.request.POST)
        input()
        return super().form_valid(form)

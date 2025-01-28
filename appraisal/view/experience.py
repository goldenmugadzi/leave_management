from typing import Dict
from django.forms import BaseModelForm
from django.http import HttpResponse
from django.http import JsonResponse
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic import TemplateView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.urls import reverse

from ..models import Experience, AppraisalExperience
from ..forms import ExperienceForm, AppraisalExperienceForm, AppraisalExperienceUpdateForm
from ..repository import AppraisalExperienceRepository, AppraisalRepository
from ..services import AppraisalExperienceService, AppraisalService
from loguru import logger

class ExperienceCreateView(CreateView):
    """View for creating new Experiences"""
    model = Experience
    form_class = ExperienceForm
    template_name = 'appraisal/experience/create.html'

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        self.object = form.save()
        
        if self.request.POST.get("popup"):
            # JSON response that inject JavaScript to close the popup and refresh the parent
            js_injector = "<script>opener.refreshExperienceDropdown(); window.close();</script>"
            return HttpResponse(js_injector)
        return super().form_valid(form)
    

class ExperienceListView(TemplateView):
    model = Experience
    template_name = 'appraisal/experience/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        appraisal_id = self.kwargs.get("appraisal_id")
        repo = AppraisalExperienceRepository()
        service_handler = AppraisalExperienceService(appraisal_repo=repo)
        context["experience_objects"] = service_handler.get_by_appraisal_id_use_case(appraisal_id=appraisal_id)
        return context
    


def experience_list_api(request):
    """
    API endpoint to retrieve a list of all experiences.

    This view retrieves all experience records from the database, selecting 
    the `id`, `name`, and `created_date` fields. The experiences are ordered 
    by the `created_date` in descending order (newest first). The data is then 
    returned in JSON format as a response.

    Args:
        request: The HTTP request object. It is passed by Django when the API 
                 endpoint is called. This argument is unused in the function 
                 but is required by Django's view system.

    Returns:
        JsonResponse: A JSON response containing a list of experiences, with 
                      fields `id`, `name`, and `created_date`. The response 
                      is set to `safe=False` to allow the serialization of 
                      non-dict objects (in this case, a list of dictionaries).

    Example:
        GET /api/experiences/
        Response:
        [
            {"id": 1, "name": "Experience 1", "created_date": "2024-11-01T12:00:00"},
            {"id": 2, "name": "Experience 2", "created_date": "2024-10-20T09:30:00"},
            ...
        ]
    """
    experiences = Experience.objects.all().values("id", "name", "created_date").order_by("-created_date")
    return JsonResponse(list(experiences), safe=False)

class AppraisalExperienceCreateView(SuccessMessageMixin, CreateView):
    model = AppraisalExperience
    form_class = AppraisalExperienceForm
    template_name = 'appraisal/experience/appraisal_experience/create.html'
    success_message = 'Experience added successfully'
    context_object_name = "appraisal_experience_form"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[self.context_object_name] = self.get_form()
        context["is_update"] = False
        return context
    
    def form_valid(self, form):
        try:
            appraisal_repository = AppraisalRepository()
            appraisal_object = appraisal_repository.get_appraisal_by_pk(appraisal_id=self.kwargs.get('appraisal_id'))
            exp_obj = form.cleaned_data.get("experience")
            years = form.cleaned_data.get("years_of_experience")
            months = form.cleaned_data.get("months_of_experience")
            appraisal_exp_repo = AppraisalExperienceRepository()
            appraisal_exp_service = AppraisalExperienceService(appraisal_repo=appraisal_exp_repo)
            
            appraisal_exp_obj = appraisal_exp_service.create_use_case(appraisal_object=appraisal_object.first(), experience_object=exp_obj, years=years, months=months)
            if appraisal_exp_obj is None:
                messages.error(self.request, "Experience already exists")
                return self.form_invalid(form)
            form.instance = appraisal_exp_obj
        except Exception as e:
            messages.error(self.request, f"An unexpected error occurred, please try again")
            logger.error(f"Creating AppraisalExperience failed with error: {e}")
            return self.form_invalid(form)
        return super().form_valid(form)
    
    def get_success_url(self) -> str:
        return reverse('update_appraisal', kwargs={"pk": self.kwargs.get('appraisal_id')})

class AppraisalExperienceUpdateView(SuccessMessageMixin, UpdateView):
    model = AppraisalExperience
    form_class = AppraisalExperienceUpdateForm
    template_name = 'appraisal/experience/appraisal_experience/create.html'
    success_message = 'Experience updated successfully'
    context_object_name = "appraisal_experience_form"
    
    def get_object(self, queryset=None):
        appraisal_exp_repo = AppraisalExperienceRepository()
        appraisal_exp_service = AppraisalExperienceService(appraisal_repo=appraisal_exp_repo)
        
        appraisal_exp_obj = appraisal_exp_service.get_by_pk_use_case(
            appraisal_exp_id=self.kwargs.get("appraisal_exp_id")
        )
        return appraisal_exp_obj
    
    def approval_user_roles(self)->Dict[str, bool]:
        is_appraisee = self.request.user == self.get_object().appraisal.user
        data = {
            "is_appraisee": is_appraisee,
        }
        return data

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[self.context_object_name] = context.get("form")
        context["is_update"] = True
        context.update(self.approval_user_roles())
        return context
        
    def form_valid(self, form):
        try:
            years = form.cleaned_data.get("years_of_experience")
            months = form.cleaned_data.get("months_of_experience")
            appraisal_exp_repo = AppraisalExperienceRepository()
            appraisal_exp_service = AppraisalExperienceService(appraisal_repo=appraisal_exp_repo)
            appraisal_exp_obj = appraisal_exp_service.update_use_case(experience_object_id=self.kwargs.get("appraisal_exp_id"), years_of_experience=years, months_of_experience=months)
            
            form.instance = appraisal_exp_obj
            
        except Exception as e:
            messages.error(self.request, "An unexpected error occurred, please try again")
            logger.error(f"Updating AppraisalExperience failed with error: {e}")
            return self.form_invalid(form)
        return super().form_valid(form)
    
    
    def get_success_url(self) -> str:
        return reverse('appraisal_experience_update', kwargs={"appraisal_exp_id": self.kwargs.get('appraisal_exp_id')})

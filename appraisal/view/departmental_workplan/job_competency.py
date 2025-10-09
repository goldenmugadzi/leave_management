from typing import Any, Dict, List
from django.forms import BaseModelForm
from django.http import HttpResponse
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic import TemplateView
from django.urls import reverse, reverse_lazy
from django.utils.text import slugify

from django.shortcuts import redirect
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from ...repository.departmental_workplan import JobCompetencyRepository
from ...models import JobCompetency
from ...forms.departmental_plan import JobCompetencyForm
from ...services.department_workplan import DepartmentOutputService
from it.users.models import Designations
from loguru import logger

def get_designation_object(designation_id):
    try:
        qr = Designations.objects.filter(id=designation_id)
        return qr.first()
    except Exception as e:
        raise Exception(f"[get_designation_object] by pk: {designation_id}, failed with error: {e}")


class JobCompetencyTemplateView(TemplateView):
    template_name = 'appraisal/departmental_workplan/job_competency/index.html'
    
    def fetch_this_year_job_competency(self):
        repo = JobCompetencyRepository()
        return repo.fetch_by_designation_id_year(
            designation_id=self.kwargs.get("designation_id"),
            year=self.kwargs.get("year")
        )
    
    def get_job_competency_form(self, request):
        return JobCompetencyForm(request)
    
    def get_designation_object(self):
        return get_designation_object(designation_id=self.kwargs.get("designation_id"))
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["job_competency_qr"] = self.fetch_this_year_job_competency()
        context["designation_object"] = self.get_designation_object()
        context["year"] = self.kwargs.get("year")
        context["job_competency_form"] = self.get_job_competency_form(None)
        return context
    
    def post(self, request, *args, **kwargs):
        try:
            designation_obj = self.get_designation_object()
            
            form = self.get_job_competency_form(
                request.POST
                )
            if form.is_valid():
                repo = JobCompetencyRepository()
                repo.create(
                    designation_obj=designation_obj,
                    required_competency=form.cleaned_data.get("required_competency")
                    )
                messages.success(request, f"Job competency added successfully")
            else:
                error_messages = ""
                for error_message in form.errors:
                    msg = f"{error_message['msg']}: '{error_message['loc'][0]}'"
                    error_messages.join(msg)
                messages.error(request, error_messages)
        except Exception as e:
            logger.error(f"[JobCompetencyTemplateView] get_designation_object() with designation_obj pk: {self.kwargs.get('designation_id')}, failed with error: {e}")
            messages.error(request, "Something went wrong, please contact the admin")

        return redirect(reverse("job_competency_index", kwargs={"designation_id": self.kwargs.get("designation_id"), "year": self.kwargs.get("year")}))

    
    def get(self, request, *args, **kwargs):
        try:
            self.object = None
            designation_obj = self.get_designation_object()
            
            if designation_obj is None:
                logger.warning(f"[JobCompetencyTemplateView] get_designation_object() with designation_obj pk: {self.kwargs.get('designation_id')}, not found error")
                return redirect("object_not_found_error", object_name=slugify("Designation"))

        except Exception as e:
            logger.error(f"[JobCompetencyTemplateView]  get_designation_object() with designation_obj pk: {self.kwargs.get('designation_id')}, failed with error: {e}")
            return redirect("server_error_view")
        return super().get(request, *args, **kwargs)


class JobCompetencyUpdateDetailView(SuccessMessageMixin, UpdateView):
    model = JobCompetency
    form_class = JobCompetencyForm
    success_message = "Job competency was updated successfully!"
    template_name = 'appraisal/departmental_workplan/job_competency/create_update.html'
    context_object_name = "job_competency_form"
    
    def get_object(self, queryset = None):
        repo = JobCompetencyRepository()
        return repo.get_by_id(pk=self.kwargs.get("job_competency_id"))
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs) 
        context[self.context_object_name] = context.get("form")
        return context
    
    def form_valid(self, form):
        try:
            repo = JobCompetencyRepository()
            obj = repo.update(
                job_competency_obj=self.get_object(),
                required_competency=form.cleaned_data.get("required_competency")
            )
            form.instance = obj
        except Exception as e:
            logger.error(f"[JobCompetencyUpdateDetailView] job_compentency_obj() with pk: {self.kwargs.get('job_competency_id')}, failed with error: {e}")
            messages.error(self.request, f"An unexpected error occurred, please try again")
            return self.form_invalid(form)

        return super().form_valid(form)
    
    def get(self, request, *args, **kwargs):
        try:
            job_compentency_obj = self.get_object()
            self.object = job_compentency_obj
            
            if job_compentency_obj is None:
                logger.warning(f"[JobCompetencyUpdateDetailView] job_compentency_obj() with pk: {self.kwargs.get('job_competency_id')}, not found error")
                return redirect("object_not_found_error", object_name=slugify("Designation"))

        except Exception as e:
            logger.error(f"[JobCompetencyUpdateDetailView]  job_compentency_obj() with pk: {self.kwargs.get('job_competency_id')}, failed with error: {e}")
            return redirect("server_error_view")
        return super().get(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse('job_competency_detail_update', kwargs={"job_competency_id": self.kwargs.get('job_competency_id')})

 
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
from ...repository.departmental_workplan import DepartmentalOutRepository, DepartmentalObjectiveRepository
from ...models import DepartmentOutput
from ...forms.departmental_plan import DepartmentOutputCreateForm, DesignationFilterForm
from ...services.department_workplan import DepartmentOutputService
from ..helper import PayloadDeserializationStrategyContext, DepartmentOutputDeserializationStrategy
from it.users.models import Designations
from loguru import logger

def get_dept_output_weight_progress(dept_objective_id: int, designation_id: int):
    handler = DepartmentOutputService(repo=DepartmentalOutRepository())
    return handler.get_designation_weight_progress(dept_objective_id=dept_objective_id, designation_id=designation_id)

def get_designation_from_filter(request)->int:
    quary_param_designation_id = request.GET.get("designations")
    designation_id = quary_param_designation_id
    if quary_param_designation_id is None:
        requester_designation_obj = request.user.designation
        designation_id = requester_designation_obj.id
    return int(designation_id)

def get_designation_by_id(designation_id: int)->Designations:
    qr = Designations.objects.filter(id=designation_id)
    if not qr.exists():
        return None
    return qr.first()

class DepartmentOutputTemplateView(TemplateView):
    template_name = 'appraisal/departmental_workplan/outputs/index.html'
    
    def get_department_objective_obj(self):
        repo = DepartmentalObjectiveRepository()
        return repo.get_by_id(dept_objective_id=self.kwargs.get("departmental_objective_id"))
    
    def get_all_outputs(self):
        repo = DepartmentalOutRepository()
        return repo.fetch_by_department_objective_and_designation_id(department_objective_id=self.kwargs.get("departmental_objective_id"), designation_id=self.get_designation_id())
    
    def get_designation_id(self):
        return get_designation_from_filter(request=self.request)
    
    def get_designation_obj(self):
        return get_designation_by_id(designation_id=self.get_designation_id())
       
    def get_designation_form(self):
        cost_center_id = self.get_department_objective_obj().cost_center.id
        return DesignationFilterForm(
                                    self.request.GET or None,  # So selected values persist
                                    cost_center_id=cost_center_id
                                    )
    
    def get_output_weight_progress(self):
        return get_dept_output_weight_progress(dept_objective_id=self.kwargs.get("departmental_objective_id"), designation_id=self.get_designation_id())
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        dept_output_weight_progress = self.get_output_weight_progress()
        dept_output_progress_data = {
            "weight": 100,
            "covered_weight": dept_output_weight_progress.covered_weight,
            "remain_weight": dept_output_weight_progress.remaining_weight
        }
        context.update(**dept_output_progress_data)
        context["designation_form"] = self.get_designation_form()
        context["designation_obj"] = self.get_designation_obj()
        context["departmental_outs_qr"] = self.get_all_outputs()
        context["department_objective"] = self.get_department_objective_obj()
        return context

    def get(self, request, *args, **kwargs):
        self.object = None
        try:
            
            if self.get_department_objective_obj() is None:
                logger.warning(f"[DepartmentOutputTemplateView] get_department_objective_obj() with department_objective pk: {self.kwargs.get('departmental_objective_id')}, not found error")
                return redirect("object_not_found_error", object_name=slugify("Department objective"))
            
            if self.get_designation_obj() is None:
                logger.warning(f"[DepartmentOutputTemplateView] get_designation_obj() with pk: {self.get_designation_obj()}, not found error")
                return redirect("object_not_found_error", object_name=slugify("Designation"))
        except Exception as e:
            logger.error(f"[DepartmentOutputTemplateView] get_department_objective_obj() with department_objective pk: {self.kwargs.get('departmental_objective_id')}, failed with error: {e}")
            return redirect("server_error_view")
        return super().get(request, *args, **kwargs)
    
class DepartmentOutputCreateView(SuccessMessageMixin, CreateView):
    model = DepartmentOutput
    form_class = DepartmentOutputCreateForm
    success_message = "Output was created successfully!"
    template_name = 'appraisal/departmental_workplan/outputs/create_update.html'
    context_object_name = "departmental_output_form"
    
    def get_department_objective_obj(self):
        repo = DepartmentalObjectiveRepository()
        return repo.get_by_id(dept_objective_id=self.kwargs.get("departmental_objective_id"))
    
    def get_designation_obj(self):
        return get_designation_by_id(designation_id=self.kwargs.get("designation_id"))
    
    def get_output_weight_progress(self):
        return get_dept_output_weight_progress(dept_objective_id=self.kwargs.get("departmental_objective_id"), designation_id=self.kwargs.get("designation_id"))
    
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[self.context_object_name] = context.get("form")
        dept_output_weight_progress = self.get_output_weight_progress()
        dept_output_progress_data = {
            "weight": 100,
            "covered_weight": dept_output_weight_progress.covered_weight,
            "remain_weight": dept_output_weight_progress.remaining_weight
        }
        context.update(**dept_output_progress_data)
        
        context["department_objective"] = self.get_department_objective_obj()
        context["designation_obj"] = self.get_designation_obj()
        return context
    
    def payload_validation(self, form):
        payload_strategy = PayloadDeserializationStrategyContext(strategy=DepartmentOutputDeserializationStrategy())
        return payload_strategy.deserialize_payload(request_object=self.request, form_object=form)
        
    def form_valid(self, form):
        try:
            payload = self.payload_validation(form=form)
            
            dept_output_weight_progress = self.get_output_weight_progress()
            if dept_output_weight_progress.remaining_weight < payload.weight:
                messages.error(self.request, "The department output weight cannot be greater than its departmental objective weight. Please adjust the department output weight to ensure it does not exceed the departmental objective weight.")
                return self.form_invalid(form)
            input()
            repo = DepartmentalOutRepository()
            dept_output_obj = repo.create(
                                            creator=self.request.user,
                                            designation_obj=self.get_designation_obj(),
                                            departmental_objective_obj=self.get_department_objective_obj(),
                                            data=payload
                                        )
            form.instance = dept_output_obj
        except Exception as e:
            logger.error(f"[DepartmentOutputCreateView] with objective id: {self.kwargs.get('departmental_objective_id')}, failed with error: {e}")
            messages.error(self.request, f"An unexpected error occurred, please try again")
            return self.form_invalid(form)

        return super().form_valid(form)

    def get(self, request, *args, **kwargs):
        self.object = None
        try:
            self.get_output_weight_progress()
            
            if self.get_designation_obj() is None:
                logger.warning(f"[DepartmentOutputCreateView] get_designation_obj() with pk: {self.kwargs.get('designation_id')}, not found error")
                return redirect("object_not_found_error", object_name=slugify("Department objective"))

            if self.get_department_objective_obj() is None:
                logger.warning(f"[DepartmentOutputCreateView] get_department_objective_obj() with department_objective pk: {self.kwargs.get('departmental_objective_id')}, not found error")
                return redirect("object_not_found_error", object_name=slugify("Department objective"))
        except Exception as e:
            logger.error(f"[DepartmentOutputCreateView] get_department_objective_obj() with department_objective pk: {self.kwargs.get('departmental_objective_id')}, failed with error: {e}")
            return redirect("server_error_view")
        return super().get(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse('departmental_output_index', kwargs={"departmental_objective_id": self.kwargs.get('departmental_objective_id')})

class DepartmentOutputDetailUpdateView(SuccessMessageMixin, UpdateView):
    model = DepartmentOutput
    form_class = DepartmentOutputCreateForm
    success_message = "Output was updated successfully!"
    template_name = 'appraisal/departmental_workplan/outputs/create_update.html'
    context_object_name = "departmental_output_form"
    
    def get_object(self, queryset=None):
        repo = DepartmentalOutRepository()
        return repo.get_by_id(dept_output_id=self.kwargs.get("department_output_id"))
        
    def get_output_weight_progress(self):
        return get_dept_output_weight_progress(dept_objective_id=self.get_object().department_objective.id, designation_id=self.kwargs.get('designation_id'))
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[self.context_object_name] = context.get("form")
        dept_output_weight_progress = self.get_output_weight_progress()
        dept_output_progress_data = {
            "weight": 100,
            "covered_weight": dept_output_weight_progress.covered_weight,
            "remain_weight": dept_output_weight_progress.remaining_weight
        }
        context.update(**dept_output_progress_data)
        
        context["department_objective"] = self.get_object().department_objective
        context["designation_obj"] = self.get_object().designation
        return context
    
    def payload_validation(self, form):
        payload_strategy = PayloadDeserializationStrategyContext(strategy=DepartmentOutputDeserializationStrategy())
        return payload_strategy.deserialize_payload(request_object=self.request, form_object=form)
        
    def form_valid(self, form):
        try:
            payload = self.payload_validation(form=form)
            
            dept_output_weight_progress = self.get_output_weight_progress()
            if dept_output_weight_progress.remaining_weight < payload.weight:
                messages.error(self.request, "The department output weight cannot be greater than its departmental objective weight. Please adjust the department output weight to ensure it does not exceed the departmental objective weight.")
                return self.form_invalid(form)

            repo = DepartmentalOutRepository()
            dept_output_obj = repo.update(
                                            updater=self.request.user,
                                            department_output_obj=self.get_object(),
                                            department_objective_obj=form.cleaned_data.get("department_objective"),
                                            data=payload
                                        )
            form.instance = dept_output_obj
        except Exception as e:
            logger.error(f"[DepartmentOutputDetailUpdateView] with department output id: {self.kwargs.get('department_output_id')}, failed with error: {e}")
            messages.error(self.request, f"An unexpected error occurred, please try again")
            return self.form_invalid(form)

        return super().form_valid(form)

    def get(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
            self.get_output_weight_progress()
            
            if self.object is None:
                logger.warning(f"[DepartmentOutputDetailUpdateView] department out with pk: {self.kwargs.get('department_output_id')}, not found error")
                return redirect("object_not_found_error", object_name=slugify("Department output"))
        except Exception as e:
            logger.error(f"[DepartmentOutputDetailUpdateView] department out with pk: {self.kwargs.get('department_output_id')}, failed with error: {e}")
            return redirect("server_error_view")
        return super().get(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse('departmental_output_detail_update', kwargs={"department_output_id": self.kwargs.get('department_output_id'), "designation_id": self.kwargs.get('designation_id')})

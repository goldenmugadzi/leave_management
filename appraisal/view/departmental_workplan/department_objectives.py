from typing import Any, Dict, List
from django.forms import BaseModelForm
from django.http import HttpResponse
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic import TemplateView
from django.urls import reverse, reverse_lazy

from django.shortcuts import redirect, render
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from it.users.models import CostCenter
from ...forms.departmental_plan import CostCenterFilterForm, DepartmentObjectiveCreateForm, DepartmentObjectiveUpdateForm
from ...models import DepartmentObjective
from ...repository.departmental_workplan import DepartmentalObjectiveRepository
from ...repository.roles import AppraisalRoleRepository
from ..helper import extended_date_rules
from loguru import logger
from datetime import datetime

class DepartmentObjectiveTemplateView(TemplateView):
    template_name = 'appraisal/departmental_workplan/index.html'
    
    def get_cost_center_form(self):
        form = CostCenterFilterForm(self.request.POST or None)
        return form
    
    def get_user_cost_center_objectives(self):
        current_year = datetime.now().year
        user_obj = self.request.user
        user_cost_center = user_obj.cost_center
        
        if user_cost_center is None:
            logger.warning(f"DepartmentObjectiveTemplateView, user pk: {user_obj}, has no cost center.")
            user_cost_center = None
        
        return user_cost_center, current_year
        
    def get_filtered_cost_center_and_year(self):
        quary_param_cost_center_id = self.request.GET.get("cost_center")
        
        cost_center_obj = None
        cost_center_qr = CostCenter.objects.filter(id=quary_param_cost_center_id)

        if cost_center_qr.exists():
            cost_center_obj = cost_center_qr.first()
            
        quary_param_year = self.request.GET.get("year")
        return cost_center_obj, quary_param_year
    
    def get_cost_center_and_year(self):
        cost_center, year = self.get_filtered_cost_center_and_year()
        if cost_center is None and year is None:
            cost_center, year = self.get_user_cost_center_objectives()

        return cost_center, year
        
    
    def get_all_departmental_objectives(self):
        cost_center, year = self.get_cost_center_and_year()

        if cost_center is None:
            return []
        
        repo = DepartmentalObjectiveRepository()
        return repo.fetch_by_cost_center_year(cost_center_id=cost_center.id, year=year)
    
    def is_section_head(self):
        repo = AppraisalRoleRepository()
        dept_objectives_qr = self.get_all_departmental_objectives()
        if not dept_objectives_qr.exists():
            return repo.is_section_head(user_id=self.request.user.id, cost_center_id=self.request.user.cost_center.id)
        else:
            obj = dept_objectives_qr.first()
            return repo.is_section_head(user_id=self.request.user.id, cost_center_id=obj.cost_center.id)
            
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cost_center, year = self.get_cost_center_and_year()
        context["cost_center_obj"] = cost_center
        context["year"] = year
        context["cost_center_form"] = self.get_cost_center_form()
        context["departmental_objectives_qr"] = self.get_all_departmental_objectives()
        context["is_section_head"] = self.is_section_head()
        
        return context
    

class DepartmentObjectiveCreateView(SuccessMessageMixin, CreateView):
    model = DepartmentObjective
    form_class = DepartmentObjectiveCreateForm
    success_message = "Objective was created successfully!"
    template_name = 'appraisal/departmental_workplan/create_update.html'
    context_object_name = "departmental_objective_form"
    success_url = reverse_lazy('departmental_workplan_index')
    
    def is_section_head(self):
        repo = AppraisalRoleRepository()
        return repo.is_section_head(user_id=self.request.user.id, cost_center_id=self.request.user.cost_center.id)
    
    def date_rules(self):
        return extended_date_rules()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[self.context_object_name] = context.get("form")
        context["is_section_head"] = self.is_section_head()
        return context
    
    def form_valid(self, form):
        try:
            creator = self.request.user
            kra_obj = form.cleaned_data.get("key_result_area")
            cost_center_obj = form.cleaned_data.get("cost_center")
            objective_description = form.cleaned_data.get("objective_description")
            
            if self.request.user.cost_center != cost_center_obj:
                messages.error(self.request, f"You are only authorized to create objectives for your department, section, or cost center.")
                return super().form_invalid(form)
            
            departmental_objective_obj = None
            repo = DepartmentalObjectiveRepository()
            is_within, prev_year_date = self.date_rules()
            if is_within:
                departmental_objective_obj = repo.create(creator=creator, key_result_area=kra_obj, cost_center=cost_center_obj, department_objective_desc=objective_description, creation_date=prev_year_date)
            else:
                departmental_objective_obj = repo.create(creator=creator, key_result_area=kra_obj, cost_center=cost_center_obj, department_objective_desc=objective_description)
            
            if departmental_objective_obj is None:
                raise Exception("department objective not created.")
            
            form.instance = departmental_objective_obj
        except Exception as e:
            logger.error(f"DepartmentObjectiveCreateView create failed with error: {e}")
            messages.error(self.request, f"An unexpected error occurred, please try again")
            return super().form_invalid(form)
        return super().form_valid(form)
    
    def get(self, request, *args, **kwargs):
        self.object = None
        
        is_within, _ = self.date_rules()
        if is_within:
            messages.info(request, "<strong>Take Note:</strong> The department objectives you are creating applies to last year.")
                    
        return super().get(request, *args, **kwargs)
    
class DepartmentObjectiveDetailUpdateView(SuccessMessageMixin, CreateView):
    model = DepartmentObjective
    form_class = DepartmentObjectiveUpdateForm
    success_message = "Objective was updated successfully!"
    template_name = 'appraisal/departmental_workplan/create_update.html'
    context_object_name = "departmental_objective_form"
    
    def get_object(self, queryset=None):
        repo = DepartmentalObjectiveRepository()
        return repo.get_by_id(dept_objective_id=self.kwargs.get("departmental_objective_id"))
    
    def is_section_head(self):
        repo = AppraisalRoleRepository()        
        return repo.is_section_head(user_id=self.request.user.id, cost_center_id=self.get_object().cost_center.id)
    
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[self.context_object_name] = context.get("form")
        context["is_section_head"] = self.is_section_head()
        return context
    
    
    def form_valid(self, form):
        try:
            updater = self.request.user
            kra_obj = form.cleaned_data.get("key_result_area")
            objective_description = form.cleaned_data.get("objective_description")
            
            repo = DepartmentalObjectiveRepository()
            departmental_objective_obj = repo.update(dep_objective_instance=self.get_object(), update_user_obj=updater, key_result_area_obj=kra_obj, department_objective_desc=objective_description)
            form.instance = departmental_objective_obj
        except Exception as e:
            logger.error(f"DepartmentObjectiveCreateView update for departmental objective pk: {self.kwargs.get('departmental_objective_id')}, failed with error: {e}")
            messages.error(self.request, f"An unexpected error occurred, please try again")
            return super().form_invalid(form)
        return super().form_valid(form)
    
    def get(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
            if self.object is None:
                logger.warning(f"DepartmentObjectiveDetailUpdateView for departmental objective pk: {self.kwargs.get('departmental_objective_id')}, doesn`t exists")
                return redirect("server_error_view")
            
        except Exception as e:
            logger.error(f"DepartmentObjectiveDetailUpdateView for departmental objective pk: {self.kwargs.get('departmental_objective_id')}, failed with error: {e}")
            return redirect("server_error_view")
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)
    
    def get_success_url(self) -> str:
        """
        Redirects to the index page after successful update.
        """
        return reverse('departmental_workplan_update_detail', kwargs={"departmental_objective_id": self.kwargs.get('departmental_objective_id')})

    
    
    

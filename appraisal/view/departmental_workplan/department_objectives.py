from typing import Any, Dict, List
from django.forms import BaseModelForm
from django.http import HttpResponse
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic import TemplateView
from django.urls import reverse, reverse_lazy

from django.shortcuts import redirect, render
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from ...forms.departmental_plan import CostCenterFilterForm, DepartmentObjectiveCreateForm
from ...models import DepartmentObjective
from ...repository.departmental_workplan import DepartmentalObjectiveRepository
from loguru import logger
from datetime import datetime

class DepartmentObjectiveTemplateView(TemplateView):
    template_name = 'appraisal/departmental_workplan/index.html'
    
    def get_all_departmental_objectives(self):
        user_cost_center = self.request.user.cost_center
        current_year = datetime.now().year
        
        repo = DepartmentalObjectiveRepository()
        
        return repo.fetch_by_cost_center_year(cost_center_id=user_cost_center.id, year=current_year)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cost_center_form"] = CostCenterFilterForm()
        context["departmental_objectives_qr"] = self.get_all_departmental_objectives()
        return context
    
    
class DepartmentObjectiveCreateView(SuccessMessageMixin, CreateView):
    model = DepartmentObjective
    form_class = DepartmentObjectiveCreateForm
    success_message = "Objective was created successfully!"
    template_name = 'appraisal/departmental_workplan/create_update.html'
    context_object_name = "departmental_objective_form"
    success_url = reverse_lazy('departmental_workplan_index')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[self.context_object_name] = context.get("form")
        return context
    
    def form_valid(self, form):
        try:
            creator = self.request.user
            kra_obj = form.cleaned_data.get("key_result_area")
            cost_center_obj = form.cleaned_data.get("cost_center")
            objective_description = form.cleaned_data.get("objective_description")
            
            repo = DepartmentalObjectiveRepository()
            departmental_objective_obj = repo.create(creator=creator, key_result_area=kra_obj, cost_center=cost_center_obj, department_objective_desc=objective_description)
            form.instance = departmental_objective_obj
        except Exception as e:
            logger.error(f"DepartmentObjectiveCreateView create failed with error: {e}")
            messages.error(self.request, f"An unexpected error occurred, please try again")
            return super().form_invalid(form)
        return super().form_valid(form)
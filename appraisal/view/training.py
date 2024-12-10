from typing import Any, Dict, Union
from django.forms import BaseModelForm
from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic.edit import CreateView
from django.views.generic import TemplateView
from django.urls import reverse

from ..forms import InterventionStrategyFormSet, ActionsForm, CompetencyFormSet
from ..models import TrainingAndDevelopment
from ..repository import TrainingAndDevelopmentRepository
from ..services import TrainingAndDevelopmentService

class TrainingAndDevelopmentUpdateView(CreateView):
    model = TrainingAndDevelopment
    form_class = ActionsForm
    template_name = "appraisal/performance/training_development/update.html"
    
    def get_competency_form(self, training_object):
        form = CompetencyFormSet(self.request.POST or None, prefix="competency")
        return form
    
    def get_intervention_strategy_form(self, training_object):
        form = InterventionStrategyFormSet(self.request.POST or None, prefix="intervention_strategy")
        return form
    
    def get_actions_form(self, training_object):
        form = ActionsForm(self.request.POST or None, prefix="action")
        return form
    
    def get_forms_initial_data(self)->Dict[str, Any]:
        training_repo_handler = TrainingAndDevelopmentRepository()
        training_service = TrainingAndDevelopmentService(training_dev_repo=training_repo_handler)
        appraisal_id = self.kwargs.get("appraisal_id")
        quarter = self.kwargs.get("quarter")
        try:
            training_object = training_service.get_by_appraisal_id_quarter_use_case(appraisal_id=appraisal_id, quarter=quarter)
            data = {
                "competency_forms": self.get_competency_form(training_object=training_object),
                "intervention_strategy_forms": self.get_intervention_strategy_form(training_object=training_object),
                "action_form": self.get_actions_form(training_object=training_object),
            }
            return data
        except Exception as e:
            return HttpResponse("oops something went wrong")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_forms_initial_data())
        return context
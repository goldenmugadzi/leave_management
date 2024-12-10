from typing import Any, Dict, Union
from django.forms import BaseModelForm
from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic.edit import CreateView
from django.views.generic import TemplateView
from django.urls import reverse

from ..helpers.types.training import TrainingAndDevelopmentCreateUpdateType

from ..forms import InterventionStrategyFormSet, ActionsForm, CompetencyFormSet
from ..models import TrainingAndDevelopment, InterventionStrategy
from ..repository import TrainingAndDevelopmentRepository
from ..services import TrainingAndDevelopmentService

class TrainingAndDevelopmentUpdateView(CreateView):
    model = TrainingAndDevelopment
    form_class = ActionsForm
    template_name = "appraisal/performance/training_development/update.html"
    
    def get_competency_form(self, training_object):
        initial_data = [
            {"required_competency": comp.name} for comp in training_object.required_competencies.all()
        ] + [
            {"competency_gap": gap.name} for gap in training_object.competency_gaps.all()
        ]
        form = CompetencyFormSet(
            self.request.POST or None,
            initial=initial_data,
            prefix="competency"
        )
        return form
    
    def get_intervention_strategy_form(self, training_object):
        initial_data = [
            {"description": strategy.description, "category": strategy.category}
            for strategy in training_object.intervention_strategies.all()
        ]
        
        
        form = InterventionStrategyFormSet(
            self.request.POST or None,
            queryset=InterventionStrategy.objects.none(),
            initial=initial_data,
            prefix="intervention_strategy"
        )
        return form
    
    def get_actions_form(self, training_object):
        initial_data = {
            "action_recommended": training_object.action_recommended,
            "action_taken": training_object.action_taken,
        }
        form = ActionsForm(
            self.request.POST or None,
            initial=initial_data,
            prefix="action"
        )
        return form
    
    def get_training_object(self)->TrainingAndDevelopment:
        training_repo_handler = TrainingAndDevelopmentRepository()
        training_service = TrainingAndDevelopmentService(training_dev_repo=training_repo_handler)
        appraisal_id = self.kwargs.get("appraisal_id")
        quarter = self.kwargs.get("quarter")
        training_object = training_service.get_by_appraisal_id_quarter_use_case(appraisal_id=appraisal_id, quarter=quarter)

        return training_object
    
    def get_forms_initial_data(self)->Dict[str, Any]:
        
        try:
            training_object = self.get_training_object()
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
    
    def build_payload(self)->TrainingAndDevelopmentCreateUpdateType:
        payload = self.request.POST
        required_competencies = [
            {
                "name": payload.get(f"competency-{i}-required_competency")
            }
            for i in range(int(payload.get("competency-MAX_NUM_FORMS", 0)))
            if payload.get(f"competency-{i}-required_competency")
            
        ]
        competency_gaps = [
            {
                "name": payload.get(f"competency-{i}-competency_gap")
            }
            for i in range(int(payload.get("competency-MAX_NUM_FORMS", 0)))
            if payload.get(f"competency-{i}-competency_gap")
        ]
        
        intervention_strategies = [
            {
                "description": payload.get(f"intervention_strategy-{i}-description"),
                "category": payload.get(f"intervention_strategy-{i}-category")
            }
            for i in range(int(payload.get("intervention_strategy-MAX_NUM_FORMS", 0)))
            if payload.get(f"intervention_strategy-{i}-description")
        ]
        data = TrainingAndDevelopmentCreateUpdateType(
            required_competencies=required_competencies,
            competency_gaps=competency_gaps,
            intervention_strategies=intervention_strategies,
            action_recommended=payload.get("action-action_recommended"),
            action_taken=payload.get("action-action_taken")
        )
        return data
    
    def form_valid(self, form):
        payload = self.build_payload()
        training_repo_handler = TrainingAndDevelopmentRepository()
        training_service = TrainingAndDevelopmentService(training_dev_repo=training_repo_handler)
        training_dev_object = self.get_training_object()

        updated_training_object = training_service.update_use_case(training_development_object=training_dev_object, payload=payload)
        form.instance = updated_training_object
        return super().form_valid(form)
    
    def get_success_url(self) -> str:
        return reverse('performance_review_detail', args=(self.kwargs.get("appraisal_id"),))
    
        
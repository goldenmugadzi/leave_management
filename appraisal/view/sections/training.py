from typing import Any, Dict, Union, List
from django.http import HttpResponse, Http404
from django.shortcuts import render, redirect
from django.views.generic.edit import CreateView
from django.views.generic import TemplateView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.urls import reverse
from django.utils.text import slugify

from ...helpers.types.training import TrainingAndDevelopmentCreateUpdateType
from ...helpers.getters import ApprovalStagesHandler
from it.users.models import UserProfile, GRADE_CHOICES

from ...forms import InterventionStrategyFormSet, ActionsForm
from ...models import TrainingAndDevelopment, InterventionStrategy, AppraisalExperience
from ...repository import TrainingAndDevelopmentRepository
from ...repository.kra import AppraisalOutPutPerformanceDimensionScoreRepository
from ...services import TrainingAndDevelopmentService, AppraisalService, UserQualificationService, AppraisalExperienceService
from ...helpers.getters.dates import get_assessment_period
from ..helper import is_within_current_quarter
from loguru import logger

class TrainingAndDevelopmentUpdateView(SuccessMessageMixin, CreateView):
    model = TrainingAndDevelopment
    form_class = ActionsForm
    template_name = "appraisal/performance/training_development/update.html"
    success_message = "Training and Development set successfully"
    
    def get_intervention_strategy_form(self, training_object):
        initial_data = [
            {"description": strategy.description, "category": strategy.category}
            for strategy in training_object.intervention_strategies.all()
        ]
        
        form = InterventionStrategyFormSet(
            self.request.POST or None,
            queryset=training_object.intervention_strategies.all(),
            initial=initial_data,
            prefix="intervention_strategy"
        )
        return form
    
    def get_training_object(self)->TrainingAndDevelopment:
        training_repo_handler = TrainingAndDevelopmentRepository()
        appraisal_id = self.kwargs.get("appraisal_id")
        quarter = self.kwargs.get("quarter_id")
        return training_repo_handler.get_by_appraisal_id_quarter(appraisal_id=appraisal_id, quarter_id=quarter)

    
    def get_actions_form(self, training_object):
        initial_data = {
            "existence_competencies": list(training_object.existence_competencies.values_list("id", flat=True)),
            "action_recommended": training_object.action_recommended,
            "action_taken": training_object.action_taken,
        }
        training_object = self.get_training_object()
        form = ActionsForm(
            self.request.POST or None,
            designation_id=training_object.appraisal.user.designation.id,
            year=training_object.appraisal.created_date.year,
            initial=initial_data,
            prefix="action"
        )
        return form
    
    def get_competency_gaps(self):
        repo = TrainingAndDevelopmentRepository()
        return repo.fetch_competency_gaps(training_dev_obj=self.get_training_object())
    
    def approval_user_roles(self)->Dict[str, bool]:
        appraisal_object = self.get_training_object().appraisal
        is_appraiser = self.request.user == appraisal_object.appraiser
        data = {
            "is_appraiser": is_appraiser
        }
        return data
    
    def get_forms_initial_data(self)->Dict[str, Any]:
        
        try:
            training_object = self.get_training_object()
            data = {
                "intervention_strategy_forms": self.get_intervention_strategy_form(training_object=training_object),
                "action_form": self.get_actions_form(training_object=training_object)
            }
            return data
        except Exception as e:
            logger.error(e)
            return HttpResponse("oops something went wrong")
        
    def is_quarter_scored(self)->bool:
        repo = AppraisalOutPutPerformanceDimensionScoreRepository()
        qr = repo.fetch_by_appraisal_id_year_quarter_id(year_quarter_id=self.kwargs.get("quarter_id"), appraisal_id=self.kwargs.get("appraisal_id"))
        unscored_qr = qr.filter(is_scored=False)
        if unscored_qr.exists():
            return False
        return True
        
    def is_current_date_in_current_quarter(self, quarter_obj)->bool:
        return is_within_current_quarter(year=quarter_obj.year, quarter=quarter_obj.quarter)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update(self.get_forms_initial_data())
        context.update(self.approval_user_roles())
        
        quarter_obj = self.get_training_object().quarter
        context["is_quarter_scored"] = self.is_quarter_scored()
        context["quarter_obj"] = quarter_obj
        context["is_within_current_quarter"] = self.is_current_date_in_current_quarter(quarter_obj=quarter_obj)
        context["competency_gaps"] = self.get_competency_gaps()
        return context
    
    def get(self, request, *args, **kwargs):
        self.object = None
        
        try:
            training_object = self.get_training_object()
            if training_object is None:
                logger.error(f"[TrainingAndDevelopmentUpdateView] get_training_object pk-{self.kwargs.get('appraisal_id')}, Training object not found")
                return redirect("object_not_found_error", object_name=slugify("Training"))
            context = self.get_context_data(**kwargs)
            return self.render_to_response(context)
        except Exception as e:
            logger.error(f"[TrainingAndDevelopmentUpdateView] get_training_object pk-{self.kwargs.get('appraisal_id')}, failed with error: {e}")
            return redirect("server_error_view")
    
    def build_payload(self) -> TrainingAndDevelopmentCreateUpdateType:
        payload = self.request.POST

        # Existence competencies (MultiSelect sends IDs)
        existence_competencies = [
            {"id": int(comp_id)}
            for comp_id in payload.getlist("action-existence_competencies")
            if comp_id
        ]

        # Intervention strategies (formset)
        intervention_strategies = [
            {
                "description": payload.get(f"intervention_strategy-{i}-description"),
                "category": payload.get(f"intervention_strategy-{i}-category"),
            }
            for i in range(int(payload.get("intervention_strategy-TOTAL_FORMS", 0)))
            if payload.get(f"intervention_strategy-{i}-description")
        ]

        return TrainingAndDevelopmentCreateUpdateType(
            existence_competencies=existence_competencies,
            intervention_strategies=intervention_strategies,
            action_recommended=payload.get("action-action_recommended"),
            action_taken=payload.get("action-action_taken"),
        )

    def form_valid(self, form):
        payload = self.build_payload()
        training_repo_handler = TrainingAndDevelopmentRepository()
        training_service = TrainingAndDevelopmentService(training_dev_repo=training_repo_handler)
        training_dev_object = self.get_training_object()

        updated_training_object = training_service.update_use_case(training_development_object=training_dev_object, payload=payload)
        form.instance = updated_training_object
        
        if not updated_training_object.is_completed:
            updated_training_object.is_completed = True
            updated_training_object.save()
            
        # Add the success message manually (SuccessMessageMixin normally does this in form_valid)
        if hasattr(self, "success_message") and self.success_message:
            messages.success(self.request, self.success_message)

        return redirect(self.get_success_url())
    
    def get_success_url(self) -> str:
        return reverse('training_development_update', kwargs={
            "appraisal_id": self.kwargs.get("appraisal_id"),
            "quarter_id": self.kwargs.get("quarter_id")
        })
    
        
class TrainingAndDevelopmentTemplateView(TemplateView):
    template_name = "appraisal/performance/training_development/detail.html"
    
    def get_appraisal_object(self):
        repo = TrainingAndDevelopmentRepository()
        return repo.get_by_appraisal_id(appraisal_id=self.kwargs.get('appraisal_id')).appraisal
        
        
    def get_training_dev_data(self)->Dict[str, List[TrainingAndDevelopment]]:
        repo = TrainingAndDevelopmentRepository()
        qr = repo.fetch_by_appraisal_id(appraisal_id=self.kwargs.get('appraisal_id'))
        
        data = {"training_objects": qr}
        return data
    
    def get_approval_stages(self):
        try:
            appraisal_object = self.get_appraisal_object()
            handler = ApprovalStagesHandler(appraisal_id=appraisal_object.id)
            return handler.get_stages_info()
        except Exception as e:
            logger.error(f"[AppraisalUpdateView] get_approval_stages for Appraisal pk: {appraisal_object.id} failed with error: {e}")
            return None    
        
    def get_current_date_assessment(self):
        appraisal_created_date = self.get_appraisal_object().created_date
        return get_assessment_period(date_object=appraisal_created_date)
    
    def appraisee_grade(self):
        user_obj = self.get_appraisal_object().user
        
        if user_obj.grade == GRADE_CHOICES[1][1]:
            return GRADE_CHOICES[1][1]
        
        if user_obj.grade == GRADE_CHOICES[2][1]:
            return "C, D, E and F"
        return ""
    
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        appraisal_object = self.get_appraisal_object()
        context.update(self.get_approval_stages())
        context.update(self.get_training_dev_data())
        
        context["appraisal_object"] = appraisal_object
        context["appraisee_object"] = appraisal_object.user
        context["appraiser_object"] = appraisal_object.appraiser
        context["reviewer_object"] = appraisal_object.reviewer
        
        context["has_no_designation"] = appraisal_object.user.designation == None or appraisal_object.user.designation == ""
        context["assessment_period"] = self.get_current_date_assessment()
        context["is_update"] = True
        context["appraisee_grade"] = self.appraisee_grade()
        return context
    
    def get(self, request, *args, **kwargs):
        try:
            self.object = None
            appraisal_obj = self.get_appraisal_object()
            
            if appraisal_obj is None:
                logger.warning(f"[TrainingAndDevelopmentTemplateView] get_appraisal_object() with appraisal_obj pk: {self.kwargs.get('appraisal_id')}, not found error")
                return redirect("object_not_found_error", object_name=slugify("Appraisal"))

        except Exception as e:
            logger.error(f"[TrainingAndDevelopmentTemplateView]  get_appraisal_object() with appraisal_obj pk: {self.kwargs.get('appraisal_id')}, failed with error: {e}")
            return redirect("server_error_view")
        return super().get(request, *args, **kwargs)


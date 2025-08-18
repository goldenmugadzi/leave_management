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

from ...forms import InterventionStrategyFormSet, ActionsForm, CompetencyFormSet
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
    
    def get_competency_form(self, training_object):
        initial_data = []
        
        for comp in training_object.required_competencies.all():
            initial_data.append({"required_competency": comp.name})
        
        for gap in training_object.competency_gaps.all():
            initial_data.append({"competency_gap": gap.name})

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
        appraisal_id = self.kwargs.get("appraisal_id")
        quarter = self.kwargs.get("quarter_id")
        return training_repo_handler.get_by_appraisal_id_quarter(appraisal_id=appraisal_id, quarter_id=quarter)

    
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
                "competency_forms": self.get_competency_form(training_object=training_object),
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
        
        if not updated_training_object.is_completed:
            updated_training_object.is_completed = True
            updated_training_object.save()
            
        return super().form_valid(form)
    
    def get_success_url(self) -> str:
        return reverse('performance_review_detail', args=(self.kwargs.get("appraisal_id"),))
    
        
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
            handler = ApprovalStagesHandler(appraisal_id=self.kwargs.get("appraisal_id"))
            return handler.get_stages_info()
        except Exception as e:
            logger.error(f"[TrainingAndDevelopmentTemplateView] for Appraisal - {self.get_appraisal_object()} failed with error: {e}")
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


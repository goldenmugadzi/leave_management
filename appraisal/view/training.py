from typing import Any, Dict, Union, List
from django.http import HttpResponse, Http404
from django.shortcuts import render, redirect
from django.views.generic.edit import CreateView
from django.views.generic import TemplateView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.urls import reverse

from ..helpers.types.training import TrainingAndDevelopmentCreateUpdateType
from ..helpers.getters import ApprovalStagesHandler
from it.users.models import UserQualification, UserProfile

from ..forms import InterventionStrategyFormSet, ActionsForm, CompetencyFormSet
from ..models import TrainingAndDevelopment, InterventionStrategy, AppraisalExperience
from ..repository import TrainingAndDevelopmentRepository, AppraisalExperienceRepository, UserQualificationRepository, ExperienceRepository, AppraisalRepository
from ..services import TrainingAndDevelopmentService, AppraisalService, UserQualificationService, AppraisalExperienceService
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
        training_service = TrainingAndDevelopmentService(training_dev_repo=training_repo_handler)
        appraisal_id = self.kwargs.get("appraisal_id")
        quarter = self.kwargs.get("quarter")
        year = self.kwargs.get("year")
        training_object = training_service.get_by_appraisal_id_quarter_use_case(appraisal_id=appraisal_id, year=year, quarter=quarter)

        return training_object
    
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
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        handler = ActivityScoreHandler()
        data = handler.get_activity_scores_quarter_scored(appraisal_id=self.kwargs.get('appraisal_id'),
                                                              quarter=self.kwargs.get('quarter'),
                                                              year=self.kwargs.get('year'))
        context.update(data)
        context.update(self.get_forms_initial_data())
        context.update(self.approval_user_roles())
        
        return context
    
    def get(self, request, *args, **kwargs):
        self.object = None
        try:
            handler = ActivityScoreHandler()
            data = handler.get_activity_scores_quarter_scored(appraisal_id=self.kwargs.get('appraisal_id'),
                                                              quarter=self.kwargs.get('quarter'),
                                                              year=self.kwargs.get('year'))
            if not data["activity_scores_quarter_scored"] and self.approval_user_roles()["is_appraiser"]:
                messages.info(request=request, message="To complete this stage, you must score all activities for this quarter. Please ensure that each activity has a score before proceeding.")
        except Exception as e:
            logger.error(f"Scored activity for appraisal: {self.kwargs.get('appraisal_id')} quarter: {self.kwargs.get('quarter')}-{self.kwargs.get('year')}, failed with error: {e}")
            return redirect("server_error_view")
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)
    
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
        appraisal_service_handler = AppraisalService(
            appraisal_experience_repository=AppraisalExperienceRepository(),
            qualification_repository=UserQualificationRepository(),
            experience_repository=ExperienceRepository(),
            appraisal_repository=AppraisalRepository()
        )
        appraisal_id = self.kwargs.get("appraisal_id")
        qr = appraisal_service_handler.get_appraisal_by_pk_use_case(appraisal_id=appraisal_id)
        
        if not qr.exists():
            raise Http404("Appraisal not found")
        
        return qr.first()
        
    
    def get_user_info(self, appraisal_id) -> Dict[str, Union[UserProfile, UserQualification, AppraisalExperience]]:
        user_qualification_service = UserQualificationService(user_qualification_repo=UserQualificationRepository())
        appraisal_experience_service = AppraisalExperienceService(appraisal_repo=AppraisalExperienceRepository())
        
        appraisal_object = self.get_appraisal_object()
        user_qualification_objects = user_qualification_service.get_by_user_object_use_case(user_object=appraisal_object.user)
        appraisal_experience_objects = appraisal_experience_service.get_by_appraisal_id_use_case(appraisal_id=appraisal_id)
        
        
        data = {
            "user_object": appraisal_object.user,
            "user_qualification_objects": user_qualification_objects,
            "user_experience_objects": appraisal_experience_objects
        }
        return data
        
    def get_training_dev_info(self, appraisal_id)->Dict[str, List[TrainingAndDevelopment]]:
        training_repo = TrainingAndDevelopmentRepository()
        training_service_handler = TrainingAndDevelopmentService(training_dev_repo=training_repo)
        data = {"training_objects": training_service_handler.get_by_appraisal_id_use_case(appraisal_id=appraisal_id)}
        return data
    
    def get_approval_stages(self):
        try:
            handler = ApprovalStagesHandler(appraisal_id=self.kwargs.get("appraisal_id"))
            return handler.get_stages_info()
        except Exception as e:
            logger.error(f"[TrainingAndDevelopmentTemplateView] for Appraisal - {self.get_appraisal_object()} failed with error: {e}")
            return None
        
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        appraisal_id = self.kwargs.get("appraisal_id")
        
        performance_plan_info = self.get_training_dev_info(appraisal_id=appraisal_id)
        user_info = self.get_user_info(appraisal_id=appraisal_id)
        
        
        context.update(self.get_approval_stages())
        context.update(user_info)
        context.update(performance_plan_info)
        context["appraisal_object"] = self.get_appraisal_object()
        
        return context
    
    def get(self, request, *args, **kwargs):
        approval_data = self.get_approval_stages()
        if approval_data is None:
            return redirect("server_error_view")
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

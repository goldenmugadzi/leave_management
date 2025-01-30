from typing import Any, Dict, List, Union
from django.http import Http404, HttpResponseRedirect
from django.urls import reverse
from django.http.response import HttpResponse as HttpResponse

from django.views.generic import TemplateView
from ..services import (AppraisalService, PerformanceReviewService, 
                        UserQualificationService, AppraisalExperienceService, 
                        TrainingAndDevelopmentService)
from ..repository import (AppraisalRepository, UserQualificationRepository, AppraisalExperienceRepository, 
                          ExperienceRepository, PerformanceReviewRepository,
                          TrainingAndDevelopmentRepository)

from ..models import PerformanceProgressReview, AppraisalExperience, TrainingAndDevelopment
from it.users.models import UserQualification, UserProfile
from ..forms import PerformanceReviewApprovalForm
from approve.forms import ApprovalForm
from approve.models import Step, Approval
from loguru import logger


class PerformancePlanAndAssessmentAppraisalTemplateView(TemplateView):
    template_name = "appraisal/performance/index.html"
    
    
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        appraisal_service_handler = AppraisalService(
            appraisal_experience_repository=AppraisalExperienceRepository(),
            qualification_repository=UserQualificationRepository(),
            experience_repository=ExperienceRepository(),
            appraisal_repository=AppraisalRepository()
        )
        context["appraisals"] = appraisal_service_handler.get_all_use_case()

        return context
    
class PerformancePlanAndAssessmentTemplateView(TemplateView):
    template_name = "appraisal/performance/detail.html"
    
    def approve_form_data(self):
        approvalForm = None
        to = None
        completed = False
        appraisal_object = self.get_appraisal_object(appraisal_id=self.kwargs.get("appraisal_id"))
        
        if not appraisal_object.process.approval_set.filter(approved="Rejected").exists():  # and allowed:
            try:
                last_approved = appraisal_object.process.approval_set.last().step.step
            except AttributeError:
                last_approved = 0
            next_step = last_approved + 1
            try:
                newStep = Step.objects.filter(step=next_step, workflow=appraisal_object.process.workflow)
                
                if newStep.first().approver.name == "appraisee" or newStep.first().approver.name == "appraiser":
                    is_appraisee = newStep.filter(
                        approver__name="appraisee"
                    ).exists()
                    
                    is_appraiser = newStep.filter(
                        approver__name="appraiser"
                    ).exists()
                    if (is_appraisee and appraisal_object.user == self.request.user) | (is_appraiser and appraisal_object.appraiser == self.request.user):
                        approvalForm = ApprovalForm
                        to = newStep.first().to
                else:
                    allowed_to_approve = newStep.filter(
                        approver__in=self.request.user.roles.all()
                    ).exists()
                    if allowed_to_approve:
                        approvalForm = ApprovalForm
                        to = newStep.first().to
                   
                # if newStep == appraisal_object.process.workflow.step_set.last():
                #     generateTokenForm = GenerateTokenForm()
            except Exception as e:
                print("=====>>>>", e)
            completed = appraisal_object.process.workflow.step_set.last().step == last_approved
        approved_steps = appraisal_object.process.approval_set.all().values_list(
            "step__step", flat=True
        )
        return {
            "completed": completed,
            "approved_steps": approved_steps,
            "approvalForm": approvalForm,
            # "generateTokenForm": generateTokenForm,
            "to": to,
        }
    
    
    def get_appraisal_object(self, appraisal_id):
        appraisal_service_handler = AppraisalService(
            appraisal_experience_repository=AppraisalExperienceRepository(),
            qualification_repository=UserQualificationRepository(),
            experience_repository=ExperienceRepository(),
            appraisal_repository=AppraisalRepository()
        )
        appraisal_object = appraisal_service_handler.get_appraisal_by_pk_use_case(appraisal_id=appraisal_id).first()
        return appraisal_object
        
    
    def get_user_info(self, appraisal_id) -> Dict[str, Union[UserProfile, UserQualification, AppraisalExperience]]:
        user_qualification_service = UserQualificationService(user_qualification_repo=UserQualificationRepository())
        appraisal_experience_service = AppraisalExperienceService(appraisal_repo=AppraisalExperienceRepository())
        
        appraisal_object = self.get_appraisal_object(appraisal_id=appraisal_id)
        user_qualification_objects = user_qualification_service.get_by_user_object_use_case(user_object=appraisal_object.user)
        appraisal_experience_objects = appraisal_experience_service.get_by_appraisal_id_use_case(appraisal_id=appraisal_id)
        
        
        data = {}
        data["user_object"] = appraisal_object.user
        data["user_qualification_objects"] = user_qualification_objects
        data["user_experience_objects"] = appraisal_experience_objects
        
        return data
        
    def get_performance_plan_info(self, appraisal_id)->Dict[str, Union[List[PerformanceProgressReview], List[TrainingAndDevelopment]]]:
        data = {}
        
        performance_review_repository = PerformanceReviewRepository()
        performance_review_service_handler = PerformanceReviewService(performance_repo=performance_review_repository)
        performance_review_objects = performance_review_service_handler.get_performances_by_appraisal_id_use_case(appraisal_id=appraisal_id)
        data["performance_review_objects"] = performance_review_objects
        
        training_repo = TrainingAndDevelopmentRepository()
        training_service_handler = TrainingAndDevelopmentService(training_dev_repo=training_repo)
        data["training_objects"] = training_service_handler.get_by_appraisal_id_use_case(appraisal_id=appraisal_id)
        return data
    
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        appraisal_id = self.kwargs.get("appraisal_id")
        
        performance_plan_info = self.get_performance_plan_info(appraisal_id=appraisal_id)
        user_info = self.get_user_info(appraisal_id=appraisal_id)
        
        context.update(user_info)
        context.update(performance_plan_info)
        context["appraisal_object"] = self.get_appraisal_object(appraisal_id=appraisal_id)
        context.update(self.approve_form_data())
        
        return context
    
    

class PerformanceReviewsApprovalView(TemplateView):
    template_name = "appraisal/performance/progress_review/create.html"
    

    def get_performance_review_forms_objects(self) -> Dict[str, PerformanceReviewApprovalForm | List[PerformanceProgressReview | int]]:
        """
        Fetches and prepares performance review forms and objects for a given appraisal ID and quarter.

        Args:
            appraisal_id (int): The ID of the appraisal to fetch reviews for.
            quarter (int): The specific quarter for which to prepare forms.

        Returns:
            Dict[str, PerformanceReviewApprovalForm | List[PerformanceProgressReview]]: 
                A dictionary with:
                - "current_form": An instance of PerformanceReviewApprovalForm for the specified quarter.
                - "performance_review_objects": A list of PerformanceProgressReview objects.
                - "quarter": current quarter

        Raises:
            Http404: If no matching form for the specified quarter is found.
        """
        appraisal_id = self.kwargs.get("appraisal_id")
        current_quarter = self.kwargs.get("quarter")
        current_year = self.kwargs.get("year")
        
        repository = PerformanceReviewRepository()
        service_handler = PerformanceReviewService(performance_repo=repository)
        performance_review_object = service_handler.get_performances_by_appraisal_id_quarter_use_case(appraisal_id=appraisal_id, year=current_year, quarter=current_quarter)

        if performance_review_object is None:
            raise Http404("Performance Progress Review for this quarter not found")
        
        quarter = performance_review_object.quarter
        form = PerformanceReviewApprovalForm(self.request.POST or None, initial={"quarter": quarter, "strengths": performance_review_object.strengths.all(), "areas_of_weaknesses": performance_review_object.areas_of_weaknesses.all()})
        data = {
            "current_form": form,
            "current_quarter": quarter,
            "performance_review_object": performance_review_object
        }
            
        return data


        
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(self.get_performance_review_forms_objects())
        return context
    
    def post(self, request, *args, **kwargs):
        appraisal_id = self.kwargs.get("appraisal_id")
        quarter = self.kwargs.get("quarter")
    
        form = PerformanceReviewApprovalForm(request.POST)
        
        if form.is_valid():
            strengths = form.cleaned_data.get("strengths")
            weaknesses = form.cleaned_data.get("areas_of_weaknesses")
            
            repository = PerformanceReviewRepository()
            service_handler = PerformanceReviewService(performance_repo=repository)
            
            try:
                performance_review_object = service_handler.get_performances_by_appraisal_id_quarter_use_case(appraisal_id=appraisal_id, quarter=quarter)

            except Exception as e:
                logger.error(f"retrieve performance object, failed with error: {e}")
                return HttpResponse("oops something went wrong")
            
            try:
                service_handler.add_strengths_use_case(performance_review_object=performance_review_object, strengths=strengths)
            except Exception as e:
                logger.error(f"Add strengths failed with error: {e}")
                return HttpResponse("oops something went wrong")
            
            try:
                service_handler.add_weakness_use_case(performance_review_object=performance_review_object, weaknesses=weaknesses)
            except Exception as e:
                logger.error(f"Add weakness failed with error: {e}")
                return HttpResponse("oops something went wrong")
            
            return HttpResponseRedirect(reverse('performance_review_detail', args=(appraisal_id,)))

        context = self.get_context_data(**kwargs)
        context["form"] = form
        return self.render_to_response(context)
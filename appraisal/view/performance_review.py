from typing import Any, Dict, List, Union
from django.http import Http404, HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import redirect, render
from django.http.response import HttpResponse, HttpResponseServerError

from django.views.generic import TemplateView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from ..services import (AppraisalService, PerformanceReviewService, 
                        UserQualificationService, AppraisalExperienceService, 
                        TrainingAndDevelopmentService)
from ..repository import (AppraisalRepository, UserQualificationRepository, AppraisalExperienceRepository, 
                          ExperienceRepository, PerformanceReviewRepository,
                          TrainingAndDevelopmentRepository)
from ..helpers.getters import ApprovalStagesHandler

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
    
    def get_approval_stages(self):
        try:
            handler = ApprovalStagesHandler(appraisal_id=self.kwargs.get("appraisal_id"))
            return handler.get_stages_info()
        except Exception as e:
            logger.error(f"[PerformancePlanAndAssessmentTemplateView] for Appraisal - {self.get_appraisal_object()} failed with error: {e}")
            return None
        
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        appraisal_id = self.kwargs.get("appraisal_id")
        
        performance_plan_info = self.get_performance_plan_info(appraisal_id=appraisal_id)
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


class PerformanceReviewsApprovalView(SuccessMessageMixin, TemplateView):
    template_name = "appraisal/performance/progress_review/create.html"
    
    def get_performance_review_object(self):
        appraisal_id = self.kwargs.get("appraisal_id")
        current_quarter = self.kwargs.get("quarter")
        current_year = self.kwargs.get("year")
        
        repository = PerformanceReviewRepository()
        service_handler = PerformanceReviewService(performance_repo=repository)
        performance_review_object = service_handler.get_performances_by_appraisal_id_quarter_use_case(appraisal_id=appraisal_id, year=current_year, quarter=current_quarter)
        
        if performance_review_object is None:
            raise Http404("Performance Progress Review for this quarter not found")
        
        return performance_review_object
    
    def get_performance_review_forms_objects(self) -> Dict[str, PerformanceReviewApprovalForm | List[PerformanceProgressReview | int]]:
        """
        Fetches and prepares performance review forms and objects for a given appraisal ID and quarter.

        Returns:
            Dict[str, PerformanceReviewApprovalForm | List[PerformanceProgressReview]]: 
                A dictionary with:
                - "current_form": An instance of PerformanceReviewApprovalForm for the specified quarter.
                - "performance_review_objects": A list of PerformanceProgressReview objects.
                - "quarter": current quarter

        Raises:
            Http404: If no matching form for the specified quarter is found.
        """
        performance_review_object = self.get_performance_review_object()
        
        quarter = performance_review_object.quarter
        form = PerformanceReviewApprovalForm(self.request.POST or None, initial={"quarter": quarter, "strengths": performance_review_object.strengths.all(), "areas_of_weaknesses": performance_review_object.areas_of_weaknesses.all()})
        data = {
            "current_form": form,
            "current_quarter": quarter,
            "performance_review_object": performance_review_object
        }
            
        return data
    
    def approval_user_roles(self)->Dict[str, bool]:
        appraisal_object = self.get_performance_review_object().appraisal
        is_appraiser = self.request.user == appraisal_object.appraiser
        data = {
            "is_appraiser": is_appraiser
        }
        return data


    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(self.get_performance_review_forms_objects())
        context.update(self.approval_user_roles())
        return context
    
    def post(self, request, *args, **kwargs):
        appraisal_id = self.kwargs.get("appraisal_id")
        current_quarter = self.kwargs.get("quarter")
        current_year = self.kwargs.get("year")
        form = PerformanceReviewApprovalForm(request.POST)
        
        if form.is_valid():
            strengths = form.cleaned_data.get("strengths")
            weaknesses = form.cleaned_data.get("areas_of_weaknesses")
            
            performance_review_object = self.get_performance_review_object()
            repository = PerformanceReviewRepository()
            service_handler = PerformanceReviewService(performance_repo=repository)
         
            try:
                service_handler.add_strengths_use_case(performance_review_object=performance_review_object, strengths=strengths)
            except Exception as e:
                logger.error(f"Add strengths for appraisal pk: {current_quarter} and quarter: {current_year}-{current_quarter}, failed with error: {e}")
                return redirect("server_error_view")
            
            try:
                service_handler.add_weakness_use_case(performance_review_object=performance_review_object, weaknesses=weaknesses)
            except Exception as e:
                logger.error(f"Add weakness for appraisal pk: {current_quarter} and quarter: {current_year}-{current_quarter}, failed with error: {e}")
                return redirect("server_error_view")            
            
            if not performance_review_object.is_completed:
                print("============>>>>>>> hit")
                performance_review_object.is_completed = True
                performance_review_object.save()
                print("============>>>>>>> after ", performance_review_object.is_completed)
                
            messages.success(request, "Performance Review updated successfully")
            return HttpResponseRedirect(reverse('performance_review_detail', args=(appraisal_id,)))

        context = self.get_context_data(**kwargs)
        context["form"] = form
        return self.render_to_response(context)
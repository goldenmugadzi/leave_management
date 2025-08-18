from typing import Any, Dict, List, Union
from django.http import Http404, HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import redirect, render
from django.http.response import HttpResponse, HttpResponseServerError
from django.utils.text import slugify

from django.views.generic import TemplateView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from ...services import (AppraisalService, PerformanceReviewService, 
                        UserQualificationService, AppraisalExperienceService, 
                        TrainingAndDevelopmentService)
from ...repository import (AppraisalRepository, UserQualificationRepository, AppraisalExperienceRepository, 
                          ExperienceRepository, PerformanceReviewRepository,
                          TrainingAndDevelopmentRepository)
from ...helpers.getters import ApprovalStagesHandler


from ...models import PerformanceProgressReview, AppraisalExperience, TrainingAndDevelopment
from it.users.models import UserQualification, UserProfile, GRADE_CHOICES
from ...forms import PerformanceReviewApprovalForm
from approve.forms import ApprovalForm
from approve.models import Step, Approval
from ...helpers.getters.dates import get_assessment_period
from ..helper import is_within_current_quarter
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
        repo = TrainingAndDevelopmentRepository()
        return repo.get_by_appraisal_id(appraisal_id=self.kwargs.get('appraisal_id')).appraisal

        
    def get_performance_plan_info(self, appraisal_id)->Dict[str, Union[List[PerformanceProgressReview], List[TrainingAndDevelopment]]]:
        data = {}
        
        performance_review_repository = PerformanceReviewRepository()
        performance_review_objects = performance_review_repository.get_performance_by_appraisal_id(appraisal_id=appraisal_id)
        data = {"performance_review_objects": performance_review_objects}
        return data
    
        
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
        appraisal_id = self.kwargs.get("appraisal_id")
        appraisal_object = self.get_appraisal_object()

        performance_plan_info = self.get_performance_plan_info(appraisal_id=appraisal_id)
        
        context.update(performance_plan_info)
        context["appraisal_object"] = appraisal_object
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
                logger.warning(f"[PerformancePlanAndAssessmentAppraisalTemplateView] get_appraisal_object() with appraisal_obj pk: {self.kwargs.get('appraisal_id')}, not found error")
                return redirect("object_not_found_error", object_name=slugify("Appraisal"))

        except Exception as e:
            logger.error(f"[PerformancePlanAndAssessmentAppraisalTemplateView]  get_appraisal_object() with appraisal_obj pk: {self.kwargs.get('appraisal_id')}, failed with error: {e}")
            return redirect("server_error_view")
        return super().get(request, *args, **kwargs)



class PerformanceReviewsApprovalView(SuccessMessageMixin, TemplateView):
    template_name = "appraisal/performance/progress_review/create.html"
    
    def get_performance_review_object(self):
        appraisal_id = self.kwargs.get("appraisal_id")
        quarter_id = self.kwargs.get("quarter_id")
        
        repository = PerformanceReviewRepository()
        performance_review_object = repository.get_performance_by_appraisal_id_quarter(appraisal_id=appraisal_id, quarter_id=quarter_id)

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
    
    def is_quarter_scored(self)->bool:
        repo = PerformanceReviewRepository()
        qr = repo.fetch_performance_by_appraisal_id_quarter(quarter_id=self.kwargs.get("quarter_id"), appraisal_id=self.kwargs.get("appraisal_id"))
        unscored_qr = qr.filter(is_completed=False)
        if unscored_qr.exists():
            return False
        return True
    
    
    def is_current_date_in_current_quarter(self, quarter_obj)->bool:
        return is_within_current_quarter(year=quarter_obj.year, quarter=quarter_obj.quarter)
    
    
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        
        context.update(self.get_performance_review_forms_objects())
        context.update(self.approval_user_roles())
        quarter_obj = self.get_performance_review_object().quarter
        
        context["is_quarter_scored"] = self.is_quarter_scored()
        context["quarter_obj"] = quarter_obj
        context["is_within_current_quarter"] = self.is_current_date_in_current_quarter(quarter_obj=quarter_obj)
        return context
    
    def get(self, request, *args, **kwargs):
        self.object = None
        try:
            performance_review_object = self.get_performance_review_object()
            if performance_review_object is None:
                logger.error(f"[PerformanceReviewsApprovalView] get_performance_review_object pk-{self.kwargs.get('appraisal_id')}, Training object not found")
                return redirect("object_not_found_error", object_name=slugify("Performance Review"))
            context = self.get_context_data(**kwargs)
            return self.render_to_response(context)
        except Exception as e:
            logger.error(f"[TrainingAndDevelopmentUpdateView] get_performance_review_object pk-{self.kwargs.get('appraisal_id')}, failed with error: {e}")
            return redirect("server_error_view")
    
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
                performance_review_object.is_completed = True
                performance_review_object.save()
                
            messages.success(request, "Performance Review updated successfully")
            return HttpResponseRedirect(reverse('performance_review_detail', args=(appraisal_id,)))

        context = self.get_context_data(**kwargs)
        context["form"] = form
        return self.render_to_response(context)
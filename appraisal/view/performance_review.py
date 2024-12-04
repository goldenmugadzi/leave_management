from typing import Any, Dict, List
from django.http import Http404, HttpResponseRedirect
from django.urls import reverse
from django.http.response import HttpResponse as HttpResponse

from django.views.generic import TemplateView, UpdateView
from ..services.appraisal import AppraisalService
from ..services.performance import PerformanceReviewService
from ..repository import AppraisalRepository, UserQualificationRepository, AppraisalExperienceRepository, ExperienceRepository, PerformanceReviewRepository

from ..models import PerformanceProgressReview
from ..forms import PerformanceReviewApprovalForm
from loguru import logger

class PerformanceReviewsTemplateView(TemplateView):
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
    

class PerformanceReviewsApprovalView(TemplateView):
    template_name = "appraisal/performance/detail.html"
    
    def get_user_appraisal_info(self, appraisal_id: int)->dict:
        # appraisal user info
        # appraisal user qualifications
        # appraisal user experience
        return {}


    def get_performance_review_forms_objects(
        self, 
        appraisal_id: int, 
        quarter: int
    ) -> Dict[str, PerformanceReviewApprovalForm | List[PerformanceProgressReview | int]]:
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
        repository = PerformanceReviewRepository()
        service_handler = PerformanceReviewService(performance_repo=repository)
        performance_review_objects = service_handler.get_performances_by_appraisal_id_use_case(appraisal_id=appraisal_id)

        data = {}
        for performance_review_object in performance_review_objects:
            if performance_review_object.quarter == quarter:
                form = PerformanceReviewApprovalForm(self.request.POST or None, initial={"quarter": quarter})
                data["current_form"] = form
                data["current_quarter"] = quarter
                data["performance_review_objects"] = performance_review_objects
                return data

        raise Http404(f"No performance review form found for the {quarter} quarter of the year.")

        
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        appraisal_id = self.kwargs.get("appraisal_id")
        current_quarter = self.kwargs.get("quarter")
        appraisal_info = self.get_user_appraisal_info(appraisal_id=appraisal_id)
        performance_review_objects = self.get_performance_review_forms_objects(appraisal_id=appraisal_id, quarter=current_quarter)
        context.update(appraisal_info)
        context.update(performance_review_objects)
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
                performance_review_object = service_handler.get_performance_by_id_use_case(pk=appraisal_id)
            except Exception as e:
                logger.error(f"Add strengths failed with error: {e}")
                return HttpResponse("oops something went wrong")
            
            try:
                service_handler.add_strengths_use_case(performance_review_object=performance_review_object, strengths=strengths)
            except Exception as e:
                logger.error(f"Add strengths failed with error: {e}")
                return HttpResponse("oops something went wrong")
            
            try:
                service_handler.add_weakness_use_case(performance_review_object=performance_review_object, weaknesses=weaknesses)
            except Exception as e:
                logger.error(f"Add strengths failed with error: {e}")
                return HttpResponse("oops something went wrong")
            
            if quarter > 4:
                return HttpResponse("1st, 2nd, 3rd and 4th quarter of the year are required")
            
            next_quarter = quarter+1
            return HttpResponseRedirect(reverse('performance_review_detail', args=(appraisal_id, next_quarter)))

        context = self.get_context_data(**kwargs)
        context["form"] = form
        return self.render_to_response(context)
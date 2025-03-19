from typing import Any, Dict, List
from django.urls import reverse
from django.views.generic.edit import UpdateView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.http import Http404
from django.http import JsonResponse, HttpResponse
from ...models import AppraisalKraReviewerStatus
from ...models.kra import APPRAISAL_KRA_REVIEWER_STATUS_CHOICES
from ...forms import AppraisalKraReviewerStatusForm
from ...repository.kra import ApprasialKraReviewerStatusRepository
from ...helpers.getters.approval import ApprovalStagesHandler
from loguru import logger

class AppraisalKraReviewerStatusUpdateView(SuccessMessageMixin, UpdateView):
    model = AppraisalKraReviewerStatus
    form_class = AppraisalKraReviewerStatusForm
    template_name = 'appraisal/kra/reviewer_status/update.html'
    success_message = 'Reviewer status updated successfully'
    context_object_name = "appraisal_reviewer_status_form"
    
    def get_object(self, queryset = ...):
        obj = get_object_or_404(AppraisalKraReviewerStatus, appraisal_kra__id=self.kwargs.get("appraisal_kra_id"))
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[self.context_object_name] = context.get("form")
        return context

    def form_valid(self, form):
        try:
            status = form.cleaned_data.get("status")
            comment = form.cleaned_data.get("comment")
            
            if (status == APPRAISAL_KRA_REVIEWER_STATUS_CHOICES[2][0]) and (comment == "" or comment == None):
                messages.error(self.request, "Please provide the reason for your rejection in the comment field before proceeding.")
                return self.form_invalid(form) 
            
            repo = ApprasialKraReviewerStatusRepository()
            obj = repo.update(appraisal_kra_reviewer_status_obj=self.get_object(), status=status, comment=comment)
            form.instance = obj
        except Exception as e:
            logger.error(f"AppraisalKraReviewerStatusUpdateView for {self.get_object()}, failed with error: {e}")
            messages.error(self.request, "An unexpected error occurred. Please try again")
            return self.form_invalid(form)   
        
        # JSON response that inject JavaScript to close the popup and refresh the parent
        js_injector = "<script>window.close();</script>"
        return HttpResponse(js_injector)
    
    
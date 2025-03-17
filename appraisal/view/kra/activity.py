from typing import Any, Dict, List
from django.urls import reverse
from django.shortcuts import redirect
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView, UpdateView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from ...models import Activity, KeyResultArea
from ...forms import ActivityCreateForm
from ...repository.kra import KRARepository, KraActivityRepository, AppraisalKraRepository
from ...services.kra import KRAService, ActivityService
from ...helpers.types.kra import KRAType
from ...helpers.getters.approval import ApprovalStagesHandler

from django.http import Http404
from .helper import build_payload_activity
from pydantic import ValidationError
from loguru import logger


def get_appraisal_kra_object(appraisal_kra_id: int)->KeyResultArea:
    repo = AppraisalKraRepository()
    appraisal_kra_object = repo.retrieve_by_pk(pk=appraisal_kra_id)
    return appraisal_kra_object

def get_activity_weight_against_kra_weight(appraisal_kra_object):
    repo = KraActivityRepository()
    service_handler = ActivityService(activity_repo=repo)

    return service_handler.get_activities_kra_weight_progress(appraisal_kra_object=appraisal_kra_object)


class KraActivityIndexTemplateView(TemplateView):
    template_name = 'appraisal/kra/activity/index.html'

    def get_appraisal_object(self):
        kra_obj_id = self.kwargs.get('appraisal_kra_id')
        kra_obj = get_appraisal_kra_object(appraisal_kra_id=kra_obj_id)
        if kra_obj is None:
            raise Http404("No KRA object found.")
        return kra_obj.appraisal
    
    def get_activity(self):
        repo = KraActivityRepository()
        service_handler = ActivityService(activity_repo=repo)
        queryset = service_handler.fetch_by_appraisal_kra_id_use_case(appraisal_kra_id=self.kwargs.get('appraisal_kra_id'))
        data = {"activity_objects": queryset}
        return data
    
    def approval_user_roles(self)->Dict[str, bool]:
        is_appraiser = self.request.user == self.get_appraisal_object().appraiser
        data = {
            "is_appraiser": is_appraiser
        }
        return data
    
    def get_approval_stages(self):
        try:
            handler = ApprovalStagesHandler(appraisal_id=self.get_appraisal_object().id)
            return handler.get_stages_info()
        except Exception as e:
            logger.error(f"[PerformancePlanAndAssessmentTemplateView] for Appraisal - {self.get_appraisal_object()} failed with error: {e}")
            return None
        

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_activity())
        context.update(self.get_approval_stages())
        context.update(self.approval_user_roles())
        context["kra_obj"] = get_appraisal_kra_object(appraisal_kra_id=self.kwargs.get('appraisal_kra_id'))
        context["appraisal_object"] = self.get_appraisal_object()
        return context
    
    def get(self, request, *args, **kwargs):
        approval_data = self.get_approval_stages()
        if approval_data is None:
            return redirect("server_error_view")
        
        try:
            activity_qr = self.get_activity()["activity_objects"]
            if activity_qr.exists():
                appraisal_kra_object = activity_qr.first().appraisal_kra
                get_activity_weight_against_kra_weight(appraisal_kra_object=appraisal_kra_object)
        except Exception as e:
            logger.error(f"Activity weight progress against it's activities weights failed with error: {e}")
            return redirect("server_error_view")
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)


class KraActivityCreateView(SuccessMessageMixin, CreateView):
    model = Activity
    form_class = ActivityCreateForm
    template_name = 'appraisal/kra/activity/create_update.html'
    success_message = 'Activity created successfully'
    context_object_name = "activity_form"
    

    @property
    def get_appraisal_kra_object(self):
        appraisal_kra_id = self.kwargs.get('appraisal_kra_id')
        return get_appraisal_kra_object(appraisal_kra_id=appraisal_kra_id)
    
    def approval_user_roles(self)->Dict[str, bool]:
        is_appraiser = self.request.user == self.get_appraisal_kra_object.appraisal.appraiser
        data = {
            "is_appraiser": is_appraiser
        }
        return data

    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.approval_user_roles())
        context[self.context_object_name] = context.get("form")
        context["appraisal_kra_object"] = self.get_appraisal_kra_object
        return context

    def get(self, request, *args, **kwargs):
        self.object = None
        try:
            get_activity_weight_against_kra_weight(appraisal_kra_object=self.get_appraisal_kra_object)
        except Exception as e:
            logger.error(f"Activity weight progress against it's activities weights failed with error: {e}")
            return redirect("server_error_view")
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)


    def form_valid(self, form):
        try:
            payload = build_payload_activity(request=self.request, form=form)
            appraisal_kra_object = self.get_appraisal_kra_object
            
            appraisal_kra_progress = get_activity_weight_against_kra_weight(appraisal_kra_object=self.get_appraisal_kra_object)
            if appraisal_kra_progress.remaining_kra_weight < payload.weight:
                messages.error(self.request, "The activity weight cannot be greater than its KRA weight. Please adjust the activity weight to ensure it does not exceed the KRA weight.")
                return self.form_invalid(form)
            
            assigned_user = form.cleaned_data.get("assigned_user")
            repo = KraActivityRepository()
            service_handler = ActivityService(activity_repo=repo)
            activity_object = service_handler.create_use_case(
                appraisal_kra_object=appraisal_kra_object,
                assigned_user_object=assigned_user,
                data=payload
                )
            form.instance = activity_object
        except Exception:
            messages.error(self.request, f"An unexpected error occurred, please try again")
            return self.form_invalid(form)

        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse('kra_activity_index', kwargs={"appraisal_kra_id": self.kwargs.get('appraisal_kra_id')})

class KraActivityUpdateView(SuccessMessageMixin, UpdateView):
    model = Activity
    form_class = ActivityCreateForm
    template_name = 'appraisal/kra/activity/create_update.html'
    success_message = 'Activity updated successfully'
    context_object_name = "activity_form"

    
    @property
    def get_activity_object(self):
        activity_obj_id = self.kwargs.get('activity_id')
        repo = KraActivityRepository()
        activity_obj = repo.get_activity_by_id(activity_id=activity_obj_id)
        return activity_obj

    def get_object(self, queryset=None):
        """
        Override the default get_object method to retrieve the activity object using a custom service.
        """
        obj = self.get_activity_object
        return obj

    def approval_user_roles(self)->Dict[str, bool]:
        is_appraiser = self.request.user == self.get_object().appraisal_kra.appraisal.appraiser
        data = {
            "is_appraiser": is_appraiser
        }
        return data
    

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.approval_user_roles())
        context[self.context_object_name] = context.get("form")
        context["activity_object"] = self.get_activity_object
        context["appraisal_kra_object"] = self.get_activity_object.appraisal_kra
        context["user_object"] = self.request.user
    
        return context
    
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            get_activity_weight_against_kra_weight(appraisal_kra_object=self.get_activity_object.appraisal_kra)
        except Exception as e:
            logger.error(f"Activity weight progress against it's activities weights failed with error: {e}")
            return redirect("server_error_view")
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def form_valid(self, form):
        try:
            payload = build_payload_activity(request=self.request, form=form)
            activity_object = self.get_activity_object
            
            
            appraisal_kra_progress = get_activity_weight_against_kra_weight(appraisal_kra_object=self.get_activity_object.appraisal_kra)
            if appraisal_kra_progress.remaining_kra_weight < payload.weight:
                messages.error(self.request, "The activity weight cannot be greater than its KRA weight. Please adjust the activity weight to ensure it does not exceed the KRA weight.")
                return self.form_invalid(form)
           
            assigned_user_object = form.cleaned_data.get('assigned_user')

            repo = KraActivityRepository()
            service_handler = ActivityService(activity_repo=repo)
            activity_object = service_handler.update_use_case(activity_object=activity_object, assigned_user=assigned_user_object, data=payload)
            form.instance = activity_object
        except ValidationError:
            return self.form_invalid(form)
        except Exception as e:
            messages.error(self.request, f"An unexpected error occurred: {e}")
            return self.form_invalid(form)
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """
        Redirects to the index page after successful update.
        """
        activity_obj_id = self.kwargs.get("activity_id")
        return reverse('kra_activity_update', kwargs={"activity_id": activity_obj_id})

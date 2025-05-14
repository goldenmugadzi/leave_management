from typing import Any, Dict, List
from django.urls import reverse
from django.shortcuts import redirect
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView, UpdateView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from ...models import Activity, KeyResultArea, PerformanceDimension
from ...forms import ActivityCreateForm, PerformanceDimensionForm
from ...repository.kra import KraActivityRepository, AppraisalKraRepository, PerformanceDimensionRepository
from ...services.kra import ActivityService, PerformanceDimensionService
from ...helpers.getters.approval import ApprovalStagesHandler

from django.http import Http404
from .helper import build_payload_activity, PerformanceDimensionDeserializationStrategy, PayloadDeserializationStrategyContext
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

def get_activities_performance_dimension_weight_progress(activity_object):
    service_handler = PerformanceDimensionService(repo=PerformanceDimensionRepository())
    return service_handler.get_activities_performance_dimension_weight_progress(activity_object)

class KraActivityIndexTemplateView(TemplateView):
    template_name = 'appraisal/kra/activity/index.html'
    
    def get_appraisal_kra_obj(self):
        return get_appraisal_kra_object(appraisal_kra_id=self.kwargs.get('appraisal_kra_id'))
    
    def get_appraisal_object(self):
        appraisal_kra_obj = self.get_appraisal_kra_obj()
        if appraisal_kra_obj is None:
            raise Http404("No KRA object found.")
        return appraisal_kra_obj.appraisal
    
    
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
        
        appraisal_kra_progress_handler = get_activity_weight_against_kra_weight(appraisal_kra_object=self.get_appraisal_kra_obj())
        appraisal_kra_progress_data = {
            "weight": self.get_appraisal_kra_obj().get_weight,
            "covered_weight": appraisal_kra_progress_handler.covered_weight,
            "remain_weight": appraisal_kra_progress_handler.remaining_weight
        }
        
        context.update(**appraisal_kra_progress_data)
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
            get_activity_weight_against_kra_weight(appraisal_kra_object=self.get_appraisal_kra_obj())
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
        
        appraisal_kra_progress_handler = get_activity_weight_against_kra_weight(appraisal_kra_object=self.get_appraisal_kra_object)
        appraisal_kra_progress_data = {
            "weight": self.get_appraisal_kra_object.get_weight,
            "covered_weight": appraisal_kra_progress_handler.covered_weight,
            "remain_weight": appraisal_kra_progress_handler.remaining_weight
        }
        context.update(**appraisal_kra_progress_data)
  
        
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
            if appraisal_kra_progress.remaining_weight < payload.weight:
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
        except Exception as e:
            logger.error(f"[KraActivityCreateView] for appraisal kra id: {self.kwargs.get('appraisal_kra_id')}, failed with error: {e}")
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
        
        appraisal_kra_progress_handler = get_activity_weight_against_kra_weight(appraisal_kra_object=self.get_activity_object.appraisal_kra)
        appraisal_kra_progress_data = {
            "weight": self.get_activity_object.appraisal_kra.get_weight,
            "covered_weight": appraisal_kra_progress_handler.covered_weight,
            "remain_weight": appraisal_kra_progress_handler.remaining_weight
        }
        context.update(**appraisal_kra_progress_data)
  
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


class PerformanceDimensionTemplateView(TemplateView):
    template_name = 'appraisal/kra/performance_dimension/index.html'
        
    def get_activity(self):
        repo = KraActivityRepository()
        obj = repo.get_activity_by_id(activity_id=self.kwargs.get("activity_id"))
        return obj
    
    def approval_user_roles(self)->Dict[str, bool]:
        activity_obj = self.get_activity()
        is_appraiser = self.request.user == activity_obj.appraisal_kra.appraisal.appraiser
        data = {
            "is_appraiser": is_appraiser
        }
        return data
    
    def get_approval_stages(self):
        try:
            activity_obj = self.get_activity()
            handler = ApprovalStagesHandler(appraisal_id=activity_obj.appraisal_kra.appraisal.id)
            return handler.get_stages_info()
        except Exception as e:
            logger.error(f"[PerformanceDimensionTemplateView] for Activity - {self.get_activity()} failed with error: {e}")
            return None
        
    def get_all_performance_dimension(self):
        try:
            repo = PerformanceDimensionRepository()
            service_handler = PerformanceDimensionService(repo=repo)
            return service_handler.fetch_all_by_activity_id(activity_id=self.kwargs.get("activity_id"))
            
        except Exception as e:
            logger.error(f"[PerformanceDimensionTemplateView] for Activity - {self.get_activity()} failed with error: {e}")
            return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        activity_perf_progress_handler = get_activities_performance_dimension_weight_progress(activity_object=self.get_activity())
        activity_perf_dimension_progress_data = {
            "weight": self.get_activity().weight,
            "covered_weight": activity_perf_progress_handler.covered_weight,
            "remain_weight": activity_perf_progress_handler.remaining_weight
        }
        
        context.update({"activity_object": self.get_activity()})
        context.update({"performance_dimensions_qr": self.get_all_performance_dimension()})
        context.update(activity_perf_dimension_progress_data)
        context.update(self.get_approval_stages())
        context.update(self.approval_user_roles())
        
        return context
    
    def get(self, request, *args, **kwargs):
        approval_data = self.get_approval_stages()
        if approval_data is None:
            return redirect("server_error_view")
        try:
            activity_obj = self.get_activity()
            get_activities_performance_dimension_weight_progress(activity_object=activity_obj)
        except Exception as e:
            logger.error(f"Activity weight progress against it's performance dimension weights failed with error: {e}")
            return redirect("server_error_view")
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)


class PerformanceDimensionTemplateCreateView(SuccessMessageMixin, CreateView):
    model = PerformanceDimension
    form_class = PerformanceDimensionForm
    template_name = 'appraisal/kra/performance_dimension/create_update.html'
    success_message = 'Performance Dimension created successfully'
    context_object_name = "performance_form"
    
    def get_activity_object(self):
        repo = KraActivityRepository()
        obj = repo.get_activity_by_id(activity_id=self.kwargs.get("activity_id"))
        return obj
    
    def approval_user_roles(self)->Dict[str, bool]:
        activity_obj = self.get_activity_object()
        is_appraiser = self.request.user == activity_obj.appraisal_kra.appraisal.appraiser
        data = {
            "is_appraiser": is_appraiser
        }
        return data
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        activity_perf_progress_handler = get_activities_performance_dimension_weight_progress(activity_object=self.get_activity_object())
        activity_perf_dimension_progress_data = {
            "weight": self.get_activity_object().weight,
            "covered_weight": activity_perf_progress_handler.covered_weight,
            "remain_weight": activity_perf_progress_handler.remaining_weight
        }
        
        context[self.context_object_name] = context.get("form")
        context.update({"activity_object": self.get_activity_object()})
        context.update(self.approval_user_roles())
        context.update(activity_perf_dimension_progress_data)
        return context
        
    def get_deserialized_payload(self, form):
        payload_deserialization_context = PayloadDeserializationStrategyContext(strategy=PerformanceDimensionDeserializationStrategy())
        return payload_deserialization_context.deserialize_payload(request_object=self.request, form_object=form)
        
    def form_valid(self, form):
        try:
            payload = self.get_deserialized_payload(form)
            activity_object = self.get_activity_object()
            
            service_handler = PerformanceDimensionService(repo=PerformanceDimensionRepository())
            perf_dimension_object_exists = service_handler.performance_indicator_exists(activity_id=activity_object.id, performance_indicator=payload.performance_indicator)
            if perf_dimension_object_exists:
                messages.error(self.request, "Performance Dimension with this performance indicator already exists.")
                return self.form_invalid(form)
            
            weight_progress = get_activities_performance_dimension_weight_progress(activity_object=activity_object)
            if weight_progress.remaining_weight < payload.weight:
                messages.error(self.request, "The performance dimension weight cannot be greater than the activity weight. Please adjust it to ensure it does not exceed the activity weight.")
                return self.form_invalid(form)
            
            perf_dimension_object = service_handler.create_use_case(activity_obj=activity_object, data=payload)
            form.instance = perf_dimension_object
        except Exception as e:
            logger.error(f"[PerformanceDimensionTemplateCreateView] for activity pk: {self.kwargs.get('activity_id')}, failed with error: {e}")
            messages.error(self.request, "An unexpected error occurred, please try again")
            return self.form_invalid(form)

        return super().form_valid(form)
    
    def get(self, request, *args, **kwargs):
        self.object = None
        try:
            activity_obj = self.get_activity_object()
            get_activities_performance_dimension_weight_progress(activity_object=activity_obj)
        except Exception as e:
            logger.error(f"Activity weight progress against it's performance dimension weights failed with error: {e}")
            return redirect("server_error_view")
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)
    

    def get_success_url(self) -> str:
        return reverse('performance_dimension_index', kwargs={"activity_id": self.kwargs.get('activity_id')})


class PerformanceDimensionTemplateUpdateView(SuccessMessageMixin, UpdateView):
    model = PerformanceDimension
    form_class = PerformanceDimensionForm
    template_name = 'appraisal/kra/performance_dimension/create_update.html'
    success_message = 'Performance Dimension updated successfully'
    context_object_name = "performance_form"


    def get_perf_dimension_object(self):
        service_handler = PerformanceDimensionService(repo=PerformanceDimensionRepository())
        return service_handler.get_by_pk_use_case(performance_dimension_id=self.kwargs.get('performance_dimension_id'))

    def get_object(self, queryset=None):
        """
        Override the default get_object method to retrieve the activity object using a custom service.
        """
        obj = self.get_perf_dimension_object()
        return obj

    def approval_user_roles(self)->Dict[str, bool]:
        is_appraiser = self.request.user == self.get_object().activity.appraisal_kra.appraisal.appraiser
        data = {
            "is_appraiser": is_appraiser
        }
        return data
    

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        activity_object = self.get_perf_dimension_object().activity
        activity_perf_progress_handler = get_activities_performance_dimension_weight_progress(activity_object=self.get_perf_dimension_object().activity)
        activity_perf_dimension_progress_data = {
            "weight": activity_object.weight,
            "covered_weight": activity_perf_progress_handler.covered_weight,
            "remain_weight": activity_perf_progress_handler.remaining_weight
        }
        context.update(activity_perf_dimension_progress_data)
  
        context.update(self.approval_user_roles())
        context[self.context_object_name] = context.get("form")
        context["activity_object"] = activity_object
    
        return context
    
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            activity_obj = self.get_perf_dimension_object().activity
            get_activities_performance_dimension_weight_progress(activity_object=activity_obj)
        except Exception as e:
            logger.error(f"Activity weight progress against it's performance dimension weights failed with error: {e}")
            return redirect("server_error_view")
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)
    
    def get_deserialized_payload(self, form):
        payload_deserialization_context = PayloadDeserializationStrategyContext(strategy=PerformanceDimensionDeserializationStrategy())
        return payload_deserialization_context.deserialize_payload(request_object=self.request, form_object=form)


    def form_valid(self, form):
        try:
            payload = self.get_deserialized_payload(form)
            activity_object = self.get_perf_dimension_object().activity
            
            service_handler = PerformanceDimensionService(repo=PerformanceDimensionRepository())            
            weight_progress = get_activities_performance_dimension_weight_progress(activity_object=activity_object)
            if weight_progress.remaining_weight < payload.weight:
                messages.error(self.request, "The performance dimension weight cannot be greater than the activity weight. Please adjust it to ensure it does not exceed the activity weight.")
                return self.form_invalid(form)
            
            perf_dimension_object = service_handler.update_use_case(performance_dimension_object=self.get_object(), data=payload)
            form.instance = perf_dimension_object
        except Exception as e:
            logger.error(f"[PerformanceDimensionTemplateUpdateView] object with pk: {self.kwargs.get('performance_dimension_id')}, failed with error: {e}")
            messages.error(self.request, "An unexpected error occurred, please try again")
            return self.form_invalid(form)
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """
        Redirects to the index page after successful update.
        """
        return reverse('performance_dimension_update', kwargs={"activity_id": self.kwargs.get("activity_id"), "performance_dimension_id": self.kwargs.get("performance_dimension_id")})

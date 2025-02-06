from typing import Any, Dict, List
from django.urls import reverse
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView, UpdateView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from ...models import Activity, KeyResultArea
from ...forms import ActivityCreateForm
from ...repository.kra import KRARepository, KraActivityRepository
from ...services.kra import KRAService, ActivityService
from ...helpers.types.kra import KRAType
from ...helpers.getters import get_approved_steps
from django.http import Http404
from .helper import build_payload
from pydantic import ValidationError


def get_kra_object(kra_id: int)->KeyResultArea:
    repo = KRARepository()
    service_handler = KRAService(kra_repo=repo)
    return service_handler.get_kra_by_pk_use_case(kra_id=kra_id)

class KraActivityIndexTemplateView(TemplateView):
    template_name = 'appraisal/kra/activity/index.html'

    def get_appraisal_object(self):
        kra_obj_id = self.kwargs.get('kra_id')
        kra_obj = get_kra_object(kra_id=kra_obj_id)
        if kra_obj is None:
            raise Http404("No KRA object found.")
        return kra_obj.appraisal
    
    def get_approved_steps(self):
        appraisal_object = self.get_appraisal_object()
        result = get_approved_steps(process_object=appraisal_object.process)
        return result

    def get_activity(self):
        repo = KraActivityRepository()
        service_handler = ActivityService(activity_repo=repo)
        queryset = service_handler.fetch_by_kra_id_use_case(kra_id=self.kwargs.get('kra_id'))
        data = {"activity_objects": queryset}
        return data
    
    def approval_user_roles(self)->Dict[str, bool]:
        is_appraiser = self.request.user == self.get_appraisal_object().appraiser
        data = {
            "is_appraiser": is_appraiser
        }
        return data

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        kra_obj_id = self.kwargs.get('kra_id')
        context.update(self.get_activity())
        context.update(self.get_approved_steps())
        context.update(self.approval_user_roles())
        context["kra_obj"] = get_kra_object(kra_id=kra_obj_id)
        context["appraisal_object"] = self.get_appraisal_object()
        return context

class KraActivityCreateView(SuccessMessageMixin, CreateView):
    model = Activity
    form_class = ActivityCreateForm
    template_name = 'appraisal/kra/activity/create_update.html'
    success_message = 'Activity created successfully'
    context_object_name = "activity_form"

    @property
    def get_kra_object(self):
        kra_obj_id = self.kwargs.get('kra_id')
        return get_kra_object(kra_id=kra_obj_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[self.context_object_name] = context.get("form")
        context["kra_object"] = self.get_kra_object
        return context


    def form_valid(self, form):
        try:
            payload = build_payload(request=self.request, form=form)
            kra_object = self.get_kra_object

            repo = KraActivityRepository()
            service_handler = ActivityService(activity_repo=repo)
            activity_object = service_handler.create_use_case(kra_object=kra_object,
                                                              data=payload)
            form.instance = activity_object
        except Exception:
            messages.error(self.request, f"An unexpected error occurred, please try again")
            return self.form_invalid(form)

        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse('kra_activity_index', kwargs={"kra_id": self.kwargs.get('kra_id')})

class KraActivityUpdateView(SuccessMessageMixin, UpdateView):
    model = Activity
    form_class = ActivityCreateForm
    template_name = 'appraisal/kra/activity/create_update.html'
    success_message = 'Activity updated successfully'
    context_object_name = "activity_form"

    @property
    def get_activity_object(self):
        repo = KraActivityRepository()
        service_handler = ActivityService(activity_repo=repo)
        activity_obj_id = self.kwargs.get('activity_id')
        activity_obj = service_handler.get_by_id_use_case(activity_id=activity_obj_id)
        return activity_obj

    def get_object(self, queryset=None):
        """
        Override the default get_object method to retrieve the activity object using a custom service.
        """
        obj = self.get_activity_object
        return obj

    def approval_user_roles(self)->Dict[str, bool]:
        is_appraiser = self.request.user == self.get_object().kra.appraisal.appraiser
        data = {
            "is_appraiser": is_appraiser
        }
        return data

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.approval_user_roles())
        context[self.context_object_name] = context.get("form")
        context["activity_object"] = self.get_activity_object
        context["user_object"] = self.request.user
    
        return context

    def form_valid(self, form):
        try:
            payload = build_payload(request=self.request, form=form)
            activity_object = self.get_activity_object
            assigned_user_object = form.cleaned_data.get('assigned_user')
            appraiser_object = form.cleaned_data.get('appraiser')

            repo = KraActivityRepository()
            service_handler = ActivityService(activity_repo=repo)
            activity_object = service_handler.update_use_case(activity_object=activity_object, assigned_user=assigned_user_object, appraiser=appraiser_object, data=payload)
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
        kra_obj_id = self.kwargs.get("kra_id")
        activity_obj_id = self.kwargs.get("activity_id")
        return reverse('kra_activity_update', kwargs={"kra_id": kra_obj_id, "activity_id": activity_obj_id})

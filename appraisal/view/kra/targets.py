from typing import Any, Dict, List
from django.urls import reverse
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView, UpdateView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from ...models import Activity, KeyResultArea, Target
from ...forms import ActivityCreateForm, TargetCreateForm
from ...repository.kra import ActivityTargetRepository, KraActivityRepository
from ...services.kra import TargetService, ActivityService
from ...helpers.types.kra import KRAType
from .helper import build_payload_target
from pydantic import ValidationError


class TargetsIndexView(TemplateView):
    template_name = 'appraisal/kra/targets/index.html'
    
    @property
    def get_activity_object(self):
        repo = KraActivityRepository()
        service_handler = ActivityService(activity_repo=repo)
        obj = service_handler.get_by_id_use_case(activity_id=self.kwargs.get('activity_id'))
        data = {"activity_object": obj}
        return data
    
    @property
    def get_target_objects(self):
        repo = ActivityTargetRepository()
        service_handler = TargetService(target_repository=repo)
        queryset = service_handler.fetch_by_activity_use_case(activity_id=self.kwargs.get('activity_id'))
        data = {"target_objects": queryset}
        return data
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_target_objects)
        context.update(self.get_activity_object)
        return context
    
class TargetCreateView(SuccessMessageMixin, CreateView):
    model = Target
    form_class = TargetCreateForm
    template_name = 'appraisal/kra/targets/create_update.html'
    success_message = 'Target created successfully'
    context_object_name = "target_form"

    @property
    def get_activity_object(self):
        repo = KraActivityRepository()
        service_handler = ActivityService(activity_repo=repo)
        obj = service_handler.get_by_id_use_case(activity_id=self.kwargs.get('activity_id'))
        data = {"activity_object": obj}
        return data
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[self.context_object_name] = context.get("form")
        context.update(self.get_activity_object)
        return context
    
    def form_valid(self, form):
        try:
            payload = build_payload_target(request=self.request, form=form)
            activity_object = self.get_activity_object["activity_object"]
            
            repo = ActivityTargetRepository()
            service_handler = TargetService(target_repository=repo)
            target_object = service_handler.create_use_case(activity_obj=activity_object,
                                                              payload=payload)
            form.instance = target_object
        except Exception as e:
            messages.error(self.request, f"An unexpected error occurred, please try again")
            return self.form_invalid(form)
        
        return super().form_valid(form)
    
    def get_success_url(self) -> str:
        return reverse('target_index', kwargs={"activity_id": self.kwargs.get('activity_id')})

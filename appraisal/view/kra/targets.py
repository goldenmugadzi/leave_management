from typing import Any, Dict, List
from django.urls import reverse
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView, UpdateView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from ...models import Activity, KeyResultArea
from ...forms import ActivityCreateForm
from ...repository.kra import ActivityTargetRepository, KraActivityRepository
from ...services.kra import TargetService, ActivityService
from ...helpers.types.kra import KRAType
from .helper import build_payload
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
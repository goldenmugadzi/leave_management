from typing import Any, Dict, List
from django.urls import reverse
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView, UpdateView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from ..models import KeyResultArea
from ..forms import YearQuarterForm, KraCreateForm
from ..repository.kra import KRARepository
from ..services.kra import KRAService
from..helpers.types.kra import KRAType
from pydantic import ValidationError

class KraActivityIndexTemplateView(TemplateView):
    template_name = 'appraisal/kra/activity/index.html'
    
    def get_kra_object(self):
        repo = KRARepository()
        service_handler = KRAService(kra_repo=repo)
        kra_obj_id = self.kwargs.get('kra_id')
        return service_handler.get_kra_by_pk_use_case(kra_id=kra_obj_id)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["kra_obj"] = self.get_kra_object()
        return context
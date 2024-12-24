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
from .helper import build_payload
from pydantic import ValidationError

class TargetTemplateView(TemplateView):
    template_name = 'appraisal/kra/activity/index.html'
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
    
    
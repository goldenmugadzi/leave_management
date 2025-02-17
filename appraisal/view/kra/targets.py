from typing import Dict
from django.urls import reverse
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView, UpdateView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.http import Http404
from ...models import TargetScore
from ...forms import TargetScoreForm
from ...repository.kra import KraActivityRepository, TargetScoreRepository
from ...services.kra import ActivityService, TargetScoreService
from ...helpers.getters import get_approved_steps
from ...helpers.setters import set_approval_process

from .helper import build_payload_score
from pydantic import ValidationError
from it.users.models import GRADE_CHOICES
from loguru import logger


class TargetScoreUpdateView(SuccessMessageMixin, UpdateView):
    model = TargetScore
    form_class = TargetScoreForm
    template_name = 'appraisal/kra/targets/score_form.html'
    success_message = 'Scoring was set successfully'
    context_object_name = "score_form"

    @property
    def get_target_score_object(self):
        repo = TargetScoreRepository()
        service_handler = TargetScoreService(target_score_repository=repo)
        obj = service_handler.get_by_target_id_use_case(target_id=self.kwargs.get('target_id'))
        return obj

    def get_object(self, queryset=None):
        """
        Override the default get_object method to retrieve the activity object using a custom service.
        """
        obj = self.get_target_score_object
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[self.context_object_name] = context.get("form")
        context["target_score_object"] = self.get_target_score_object
        return context

    def form_valid(self, form):
        try:
            payload = build_payload_score(request=self.request, form=form)

            repo = TargetScoreRepository()
            service_handler = TargetScoreService(target_score_repository=repo)
            target_score_object = service_handler.update_use_case(target_score_obj=self.get_object(), data=payload)
            form.instance = target_score_object
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
        return reverse('target_index', kwargs={"activity_id": self.kwargs.get('activity_id')})

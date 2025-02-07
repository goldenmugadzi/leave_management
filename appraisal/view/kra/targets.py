from typing import Dict
from django.urls import reverse
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView, UpdateView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.http import Http404
from ...models import Target, TargetScore
from ...forms import TargetCreateForm, TargetScoreForm
from ...repository.kra import ActivityTargetRepository, KraActivityRepository, TargetScoreRepository
from ...services.kra import TargetService, ActivityService, TargetScoreService
from ...helpers.getters import get_approved_steps
from ...helpers.setters import set_approval_process

from .helper import build_payload_target, build_payload_score
from pydantic import ValidationError
from it.users.models import GRADE_CHOICES
from loguru import logger


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

    def get_appraisal_object(self):
        activity_obj = self.get_activity_object["activity_object"]
        if activity_obj is None:
            raise Http404("No Activity target object found.")
        
        appraisal_obj = activity_obj.kra.appraisal
        return appraisal_obj
    
    def get_approved_steps(self):
        appraisal_object = self.get_appraisal_object()
        result = get_approved_steps(process_object=appraisal_object.process)
        return result
    
    def approval_user_roles(self)->Dict[str, bool]:
        is_appraiser = self.request.user == self.get_appraisal_object().appraiser
        data = {
            "is_appraiser": is_appraiser
        }
        return data

    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_target_objects)
        context.update(self.get_activity_object)
        context.update(self.get_approved_steps())
        context.update(self.approval_user_roles())
        context["appraisal_object"] = self.get_appraisal_object()
        return context


class TargetCreateView(SuccessMessageMixin, CreateView):
    model = Target
    form_class = TargetCreateForm
    template_name = 'appraisal/kra/targets/create_update.html'
    success_message = 'Target created successfully'
    context_object_name = "target_form"
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        appraisee_object = self.get_activity_object["activity_object"].kra.appraisal.user
        if appraisee_object.grade == GRADE_CHOICES[2][1]:
            kwargs["is_above_grade_c"] = True
        else:
            kwargs["is_above_grade_c"] = False
        return kwargs

    @property
    def get_activity_object(self):
        repo = KraActivityRepository()
        service_handler = ActivityService(activity_repo=repo)
        obj = service_handler.get_by_id_use_case(activity_id=self.kwargs.get('activity_id'))
        data = {"activity_object": obj}
        return data
    
    def approval_user_roles(self)->Dict[str, bool]:
        is_appraiser = self.request.user == self.get_activity_object["activity_object"].kra.appraisal.appraiser
        data = {
            "is_appraiser": is_appraiser
        }
        return data

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[self.context_object_name] = context.get("form")
        context.update(self.approval_user_roles())
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
            logger.error(f"TargetCreateView failed: {e}")
            messages.error(self.request, f"An unexpected error occurred, please try again")
            return self.form_invalid(form)

        return super().form_valid(form)

    def get_success_url(self) -> str:
        if 'Save And Add Another' in self.request.POST:
            return reverse('target_create', kwargs={"activity_id": self.kwargs.get('activity_id')})
        return reverse('target_index', kwargs={"activity_id": self.kwargs.get('activity_id')})
        

class TargetUpdateView(SuccessMessageMixin, UpdateView):
    model = Target
    form_class = TargetCreateForm
    template_name = 'appraisal/kra/targets/create_update.html'
    success_message = 'Target updated successfully'
    context_object_name = "target_form"

    @property
    def get_target_object(self):
        repo = ActivityTargetRepository()
        service_handler = TargetService(target_repository=repo)
        target_obj = service_handler.get_by_id_use_case(target_id=self.kwargs.get('target_id'))
        return target_obj

    def get_object(self, queryset=None):
        """
        Override the default get_object method to retrieve the activity object using a custom service.
        """
        obj = self.get_target_object
        return obj
    
    def approval_user_roles(self)->Dict[str, bool]:
        appraisal_object = self.get_object().activity.kra.appraisal
        is_appraiser = self.request.user == appraisal_object.appraiser
        is_appraisee = self.request.user == appraisal_object.user
        data = {
            "is_appraiser": is_appraiser,
            "is_appraisee": is_appraisee
        }
        return data
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        appraisee_object = self.get_object().activity.kra.appraisal.user
        if appraisee_object.grade == GRADE_CHOICES[2][1]:
            kwargs["is_above_grade_c"] = True
        else:
            kwargs["is_above_grade_c"] = False
        
        if self.approval_user_roles()["is_appraisee"]:
            kwargs["is_appraisee"] = True
        else:
            kwargs["is_appraisee"] = False
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.approval_user_roles())
        context[self.context_object_name] = context.get("form")
        context["activity_object"] = self.get_target_object.activity
        context["target_object"] = self.get_target_object
        return context
    
    def set_appraisee_approval_process(self):
        """Set the Approval Process for Appraisee to Accept KRAs"""
        process_object  = self.get_target_object.activity.kra.appraisal.process
        if "Accept Target" in self.request.POST:
            set_approval_process(process_object=process_object, user_object=self.request.user)
        if "Reject Target" in self.request.POST:
            set_approval_process(process_object=process_object, user_object=self.request.user)

    def form_valid(self, form):
        try:
            payload = build_payload_target(request=self.request, form=form)
            target_object = self.get_target_object

            repo = ActivityTargetRepository()
            service_handler = TargetService(target_repository=repo)
            if "Accept Target" in self.request.POST or "Reject Target" in self.request.POST:
                target_object = service_handler.update_use_case(target_obj=target_object,
                                                            payload=payload, is_approved=True)
                
                if not repo.get_unapproved_targets_by_activity(activity_object=target_object.activity).exists():
                    # Set approval step completed if all activity targets are approved
                    self.set_appraisee_approval_process()
            elif "Save And Add Another" in self.request.POST or "Save and Add Confirm" in self.request.POST:
                target_object = service_handler.update_use_case(target_obj=target_object,
                                                            payload=payload)

            form.instance = target_object
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
        return reverse('target_update', kwargs={"activity_id": self.kwargs.get('activity_id'),
                                                "target_id": self.kwargs.get('target_id')})


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

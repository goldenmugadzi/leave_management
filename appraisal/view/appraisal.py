from typing import Any, Dict, List
from django.forms import BaseModelForm
from django.http import HttpResponse
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic import TemplateView
from django.urls import reverse
from django.shortcuts import redirect
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages

from django.urls import reverse_lazy

from ..models import Appraisal, AppraisalExperience, Experience
from it.users.models import UserQualification
from ..forms import AppraisalForm, AppraisalExperienceFormset, UserQualificationFormset, AppraisalRoleFilterForm, AppraisalUpdateForm
from ..helpers.types import AppraisalPayloadType
from ..helpers.types.kra import RoleFilterChoices
from ..repository import UserQualificationRepository, AppraisalExperienceRepository, ExperienceRepository, AppraisalRepository
from ..services import AppraisalService, AppraisalExperienceService
from ..helpers.types.kra import KraRolesType
from ..helpers.getters import get_approved_steps

from approve.views import intiate,approve_step
from approve.forms import ApprovalForm
from approve.models import Step, Approval

class AppraisalCreateView(SuccessMessageMixin, CreateView):
    model = Appraisal
    form_class = AppraisalForm
    success_message = "Appraisal created successfully! Your appraiser will review it shortly and either accept or reject it."
    template_name = 'appraisal/create.html'

    def get_initial_forms(self, user_object)->Dict[str,Any]:
        """Helper method to initialize related forms with initial data."""
        qualification_initial_object = UserQualificationFormset(self.request.POST or None,
            queryset=UserQualification.objects.none(),
            prefix="qualification")
        appraisal_experience_initial_object = AppraisalExperienceFormset(self.request.POST or None, queryset=AppraisalExperience.objects.none())
        appraiser_form = self.form_class()
        return {
            'qualification_forms': qualification_initial_object,
            'appraisal_form': appraiser_form,
            'appraisal_experience_forms': appraisal_experience_initial_object
        }

    def get_initial_user_data(self, user_object)->Dict[str, any]:
        """Helper method to set user data"""
        return {
            "user": user_object,
            "qualifications": UserQualification.objects.filter(user=user_object)
        }

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context =  super().get_context_data(**kwargs)
        user_object = self.request.user
        context.update(self.get_initial_forms(user_object=user_object))
        context.update(self.get_initial_user_data(user_object=user_object))
        context["is_update"] = False
        return context

    def build_payload(self) -> AppraisalPayloadType:
        """Builds a structured payload dictionary grouping data by form name."""
        payload = self.request.POST
        files = self.request.FILES

        qualifications = [
            {
                "name": payload.get(f"qualification-{i}-name"),
                "file": files.get(f"qualification-{i}-file")  # Extract file from request.FILES
            }
            for i in range(int(payload.get("qualification-TOTAL_FORMS", 0)))
            if payload.get(f"qualification-{i}-name")
        ]
        experiences = [
            {
                "name": Experience.objects.filter(id=payload.get(f"appraisal-{i}-experience")).values_list("name", flat=True).first(),
                "years_of_experience": payload.get(f"appraisal-{i}-years_of_experience"),
                "months_of_experience": payload.get(f"appraisal-{i}-months_of_experience")
            }
            for i in range(int(payload.get("appraisal-TOTAL_FORMS", 0)))
            if payload.get(f"appraisal-{i}-experience") and payload.get(f"appraisal-{i}-experience") != "0"
        ]
        data = AppraisalPayloadType(experiences=experiences, qualifications=qualifications)
        return data

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        user_object = self.request.user
        if not user_object.grade:
            messages.error(self.request, "Oops! Your profile has no grade set. Kindly contact admin.")
            return self.form_invalid(form)

        appraisal_service_handler = AppraisalService(
            appraisal_experience_repository=AppraisalExperienceRepository(),
            qualification_repository=UserQualificationRepository(),
            experience_repository=ExperienceRepository(),
            appraisal_repository=AppraisalRepository()
        )
        structured_payload = self.build_payload()
        appraisal_object = appraisal_service_handler.create_use_case(
            user_object=user_object,
            data=structured_payload,
            appraiser=form.instance.appraiser,
            reviewer=form.instance.reviewer
            )
        form.instance = appraisal_object

        form.instance.user = user_object
        # if len(structured_payload.experiences) == 0:
        #     # return an error
        # print("=========>>> Structured Payload:", structured_payload)
        # input()
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse('appraisal_index')


class AppraisalUpdateView(SuccessMessageMixin, UpdateView):
    model = Appraisal
    form_class = AppraisalUpdateForm
    success_message = "Appraisal reviewer was set successfully"
    template_name = "appraisal/update.html"
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        appraisal_object = self.get_object()
        loggedin_user_object = self.request.user
        
        match loggedin_user_object:
            case appraisal_object.user:
                kwargs["role"] = KraRolesType.appraisee.value
            case appraisal_object.appraiser:
                kwargs["role"] = KraRolesType.appraiser.value
        
        return kwargs
        
    
    def approval_user_roles(self)->Dict[str, bool]:
        is_appraisee = self.request.user == self.get_object().user
        is_appraiser = self.request.user == self.get_object().appraiser
        data = {
            "is_appraisee": is_appraisee,
            "is_appraiser": is_appraiser
        }
        return data
    
    def form_valid(self, form):
        role = self.get_form_kwargs().pop("role", None)
        if role == KraRolesType.appraiser.value and not self.get_object().is_accepted:
            form.instance.is_accepted = True
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        experience_repo = AppraisalExperienceRepository()
        experience_service_handler = AppraisalExperienceService(appraisal_repo=experience_repo)
        qualifications = UserQualification.objects.filter(user=self.get_object().user)
        context["experience_objects"] = experience_service_handler.get_by_appraisal_id_use_case(appraisal_id=self.get_object().id)
        context["qualification_objects"] = qualifications
        context["appraisal_object"] = self.get_object()
        
        context.update(self.approval_user_roles())
        return context
    
    def get_success_url(self):
        return reverse("update_appraisal", kwargs={"pk": self.kwargs.get("pk")})
    

class AppraisalTemplateView(TemplateView):
    template_name = 'appraisal/index.html'
    
    def get_role_filter(self)->str:
        role_filter = self.request.GET.get('role_filter')
        if role_filter is None:
            return RoleFilterChoices.MY_APPRAISAL.value
        return role_filter
    
    def get_heading_name(self)->str:
        role_filter = self.get_role_filter()
        return role_filter.capitalize().replace("_", " ")
    
    def get_role_filter_form(self)->Dict[str, AppraisalRoleFilterForm]:
        form = AppraisalRoleFilterForm(initial={"role_filter": self.get_role_filter()})
        return {"role_filter_form": form}
    
    def get_appraisals(self)->List[Appraisal]:
        appraisal_service_handler = AppraisalService(
            appraisal_experience_repository=AppraisalExperienceRepository(),
            qualification_repository=UserQualificationRepository(),
            experience_repository=ExperienceRepository(),
            appraisal_repository=AppraisalRepository()
        )
        
        match self.get_role_filter():
            case RoleFilterChoices.MY_APPRAISAL.value:
                return {"appraisals": appraisal_service_handler.get_appraisal_by_user_use_case(user_object=self.request.user)}
            case RoleFilterChoices.ASSIGNED_APPRAISALS.value:
                return {"appraisals": appraisal_service_handler.get_appraisal_by_appraiser_use_case(appraiser_object=self.request.user)}
            case RoleFilterChoices.APPRAISALS_FOR_REVIEW.value:
                return {"appraisals": appraisal_service_handler.get_appraisal_by_reviewer_use_case(reviewer_object=self.request.user)}
            case RoleFilterChoices.ALL_APPRAISALS.value:
                return {"appraisals": appraisal_service_handler.get_all_use_case()}
        
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context =  super().get_context_data(**kwargs)
        
        context.update(self.get_role_filter_form())
        context.update({"heading_name": self.get_heading_name()})
        context.update(self.get_appraisals())
        return context

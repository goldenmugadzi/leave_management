from typing import Any, Dict, List
from django.forms import BaseModelForm
from django.http import HttpResponse
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic import TemplateView
from django.urls import reverse
from django.utils.text import slugify

from django.shortcuts import redirect, render
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages

from ..models import Appraisal
from it.users.models import UserQualification, UserProfile
from ..forms import AppraisalForm, AppraisalRoleFilterForm, AppraisalUpdateForm
from ..helpers.types.kra import RoleFilterChoices
from ..repository import UserQualificationRepository, AppraisalExperienceRepository, ExperienceRepository, AppraisalRepository
from ..repository.qualification_experience import UserExperienceRepository
from ..services import AppraisalService, AppraisalExperienceService
from ..helpers.types.kra import KraRolesType
from ..helpers.getters.approval import ApprovalStagesHandler


from approve.views import intiate,approve_step
from approve.forms import ApprovalForm
from approve.models import Step, Approval
from datetime import datetime
from ..helpers.getters.dates import get_assessment_period
from loguru import logger

def get_user_by_id(user_id: int)->UserProfile:
    qr = UserProfile.objects.filter(id=user_id)
    if not qr.exists():
        return None
    return qr.first()

class AppraisalCreateView(SuccessMessageMixin, CreateView):
    model = Appraisal
    form_class = AppraisalForm
    success_message = "Appraisal created successfully! Your appraiser will review it shortly and either accept or reject it."
    template_name = 'appraisal/create_update.html'
    context_object_name = "appraisal_form"
    
    def get_user_object(self):
        return self.request.user
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["appraisee_id"] = self.get_user_object().id
        return kwargs

    def get_current_date_assessment(self):
        current_date = datetime.now()
        return get_assessment_period(date_object=current_date)
    
    def get_user_experiences(self, user_id: int):
        repo = UserExperienceRepository()
        return repo.fetch_by_user_id(user_id=user_id)
        
    def get_user_qualification(self, user_id: int):
        repo = UserQualificationRepository()
        return repo.fetch_by_user(user_id=user_id)
        

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context =  super().get_context_data(**kwargs)
        user_object = self.get_user_object()
        context[self.context_object_name] = context.get("form")
        
        context["user_object"] = user_object
        context["has_no_designation"] = self.get_user_object().designation == None or self.get_user_object().designation == ""
        context["assessment_period"] = self.get_current_date_assessment()
        
        context["user_experiences_qr"] = self.get_user_experiences(user_id=user_object.id)
        context["user_qualification_qr"] = self.get_user_qualification(user_id=user_object.id)
        context["can_mutate"] = True
        context["is_update"] = False
        return context

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        appraisee_object = self.get_user_object()
        
        if not appraisee_object.grade:
            messages.error(self.request, "Oops! Your profile has no grade set. Kindly contact admin.")
            return self.form_invalid(form)

        if not appraisee_object.designation:
            messages.error(self.request, "Oops! Your profile has no designation set. Kindly contact admin.")
            return self.form_invalid(form)
        
        if not appraisee_object.cost_center:
            messages.error(self.request, "Oops! Your profile has no cost center set. Kindly contact admin.")
            return self.form_invalid(form)
        
        appraiser_object = form.cleaned_data.get("appraiser")
        repo = AppraisalRepository()
        appraisal_object = repo.create(appraisee_object=appraisee_object, appraiser_object=appraiser_object)
        form.instance = appraisal_object
        
        return super().form_valid(form)

    def get(self, request, *args, **kwargs):
        self.object = None
        try:
            user_object = self.get_user_object()
            if user_object is None:
                logger.warning(f"[AppraisalCreateView] get_user_object() with user: {user_object}, not found error")
                return redirect("object_not_found_error", object_name=slugify("User"))

            if user_object.designation == None or user_object.designation == "":
                messages.error(
                        request,
                        "<strong>Your designation or position</strong> was not found. Please contact IT to set your designation."
                    )
            messages.info(
                request,
                "<strong>Take Note:</strong> Please ensure your profile is complete — including designation, department, qualifications, and experience — before creating an appraisal. You may add missing details and must set your appraiser as the final step."
            )
        except Exception as e:
            logger.error(f"[AppraisalCreateView] get_user_object() with user: {user_object}, failed with error: {e}")
            return redirect("server_error_view")
        return super().get(request, *args, **kwargs)

    def get_success_url(self) -> str:
        return reverse('appraisal_index')


class AppraisalUpdateView(SuccessMessageMixin, UpdateView):
    model = Appraisal
    form_class = AppraisalUpdateForm
    success_message = "Appraisal reviewer was set successfully"
    template_name = "appraisal/create_update.html"
    
    def get_object(self):
        repo = AppraisalRepository()
        return repo.get_appraisal_by_pk(appraisal_id=self.kwargs.get('appraisal_id'))
    
    def is_appraisee_requesting(self):
        appraisee_object = self.get_object().user
        is_appraisee = appraisee_object == self.request.user
        if is_appraisee:
            return appraisee_object.id
        return None
    
    def is_appraiser_requesting(self):
        appraiser_object = self.get_object().appraiser
        is_appraiser = appraiser_object == self.request.user
        if is_appraiser:
            return appraiser_object.id
        return None
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        appraisee_id = self.is_appraisee_requesting()
        appraiser_id = self.is_appraiser_requesting()
        if appraisee_id:
            kwargs["appraisee_id"] = appraisee_id
        if appraiser_id:
            kwargs["appraiser_id"] = appraiser_id
            kwargs["appraisal_appraisee_id"] = self.get_object().user.id
        return kwargs
    
    def get_current_date_assessment(self):
        appraisal_created_date = self.get_object().created_date
        return get_assessment_period(date_object=appraisal_created_date)
    
    def get_user_experiences(self, user_id: int):
        repo = UserExperienceRepository()
        return repo.fetch_by_user_id(user_id=user_id)
        
    def get_user_qualification(self, user_id: int):
        repo = UserQualificationRepository()
        return repo.fetch_by_user(user_id=user_id)
        

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context =  super().get_context_data(**kwargs)
        appraisal_object = self.get_object()
        appraisee_object = appraisal_object.user
        context[self.context_object_name] = context.get("form")
        
        context["appraiser_object"] = appraisal_object.appraiser
        context["reviewer_object"] = appraisal_object.reviewer
        context["user_object"] = appraisee_object
        context["has_no_designation"] = appraisee_object.designation == None or appraisee_object.designation == ""
        context["assessment_period"] = self.get_current_date_assessment()
        
        context["user_experiences_qr"] = self.get_user_experiences(user_id=appraisee_object.id)
        context["user_qualification_qr"] = self.get_user_qualification(user_id=appraisee_object.id)

        can_make_changes = False
        
        if self.is_appraisee_requesting() or self.is_appraiser_requesting():
            can_make_changes = True
        
        context["can_mutate"] = can_make_changes
        context["is_update"] = True
        return context
    
    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        appraisal_object = self.get_object()
        appraisee_object = appraisal_object.user
        
        if not appraisee_object.grade:
            messages.error(self.request, "Oops! Your profile has no grade set. Kindly contact admin.")
            return self.form_invalid(form)

        if not appraisee_object.designation:
            messages.error(self.request, "Oops! Your profile has no designation set. Kindly contact admin.")
            return self.form_invalid(form)
        
        if not appraisee_object.cost_center:
            messages.error(self.request, "Oops! Your profile has no cost center set. Kindly contact admin.")
            return self.form_invalid(form)
        
        appraiser_object = form.cleaned_data.get("appraiser")
        reviewer_object = form.cleaned_data.get("reviewer")
        
        repo = AppraisalRepository()
        appraisal_object = repo.update(
            appraisal_object=appraisal_object,
            appraiser_object=appraiser_object,
            reviewer_obj=reviewer_object
        )
        form.instance = appraisal_object
        
        return super().form_valid(form)

    def get(self, request, *args, **kwargs):
        try:
            appraisal_object = self.get_object()
            self.object = appraisal_object
            if appraisal_object is None:
                logger.warning(f"[AppraisalUpdateView] get_object() with appraisal pk: {appraisal_object.id}, not found error")
                return redirect("object_not_found_error", object_name=slugify("Appraisal"))

            if appraisal_object.user.designation == None or appraisal_object.user.designation == "":
                messages.error(
                        request,
                        "<strong>Appraisee's designation or position</strong> was not found. Please contact IT to set designation."
                    )
            messages.info(
                request,
                "<strong>Take Note:</strong> Please ensure appraisee's profile is complete — including designation, department, qualifications, and experience — before making updates."
            )
        except Exception as e:
            logger.error(f"[AppraisalUpdateView]  get_object() with appraisal pk: {appraisal_object.id}, failed with error: {e}")
            return redirect("server_error_view")
        return super().get(request, *args, **kwargs)

    def get_success_url(self) -> str:
        return reverse('update_appraisal', kwargs={"appraisal_id": self.kwargs.get('appraisal_id')})


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
                return {"appraisals": appraisal_service_handler.get_appraisal_by_user_use_case(user_id=self.request.user.id)}
            case RoleFilterChoices.ASSIGNED_APPRAISALS.value:
                return {"appraisals": appraisal_service_handler.get_appraisal_by_appraiser_use_case(appraiser_id=self.request.user.id)}
            case RoleFilterChoices.APPRAISALS_FOR_REVIEW.value:
                return {"appraisals": appraisal_service_handler.get_appraisal_by_reviewer_use_case(reviewer_id=self.request.user.id)}
            case RoleFilterChoices.ALL_APPRAISALS.value:
                return {"appraisals": appraisal_service_handler.get_all_use_case()}
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context =  super().get_context_data(**kwargs)
        
        context.update(self.get_role_filter_form())
        context.update({"heading_name": self.get_heading_name()})
        context.update(self.get_appraisals())
        return context


def internal_server_error_view(request):
    return render(request, "appraisal/server_errors.html", status=500)

def object_not_found_error_view(request, object_name: str):
    object_name = object_name.replace("-", " ")
    context = {
        "object_name": object_name
    }
    return render(request, "appraisal/not_found_error.html", context=context, status=404)
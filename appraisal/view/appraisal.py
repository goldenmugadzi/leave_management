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
        appraisal_service_handler = AppraisalService(
            appraisal_experience_repository=AppraisalExperienceRepository(),
            qualification_repository=UserQualificationRepository(),
            experience_repository=ExperienceRepository(),
            appraisal_repository=AppraisalRepository()
        )
        structured_payload = self.build_payload()
        process_object = intiate(None, "Appraisal")
        appraisal_object = appraisal_service_handler.create_use_case(
            user_object=user_object,
           process_object=process_object,
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
        
    def approve_form_data(self):
        approvalForm = None
        to = None
        completed = False
        
        if not self.get_object().process.approval_set.filter(approved="Rejected").exists():  # and allowed:
            try:
                last_approved = self.get_object().process.approval_set.last().step.step
            except AttributeError:
                last_approved = 0
            next_step = last_approved + 1
            try:
                newStep = Step.objects.filter(step=next_step, workflow=self.get_object().process.workflow)
                
                if newStep.first().approver.name == "appraisee" or newStep.first().approver.name == "appraiser":
                    is_appraisee = newStep.filter(
                        approver__name="appraisee"
                    ).exists()
                    
                    is_appraiser = newStep.filter(
                        approver__name="appraiser"
                    ).exists()
                    if (is_appraisee and self.get_object().user == self.request.user) | (is_appraiser and self.get_object().appraiser == self.request.user):
                        approvalForm = ApprovalForm
                        to = newStep.first().to
                else:
                    allowed_to_approve = newStep.filter(
                        approver__in=self.request.user.roles.all()
                    ).exists()
                    if allowed_to_approve:
                        approvalForm = ApprovalForm
                        to = newStep.first().to
                   
                # if newStep == self.get_object().process.workflow.step_set.last():
                #     generateTokenForm = GenerateTokenForm()
            except Exception as e:
                print("=====>>>>", e)
            completed = self.get_object().process.workflow.step_set.last().step == last_approved
        approved_steps = self.get_object().process.approval_set.all().values_list(
            "step__step", flat=True
        )
        return {
            "completed": completed,
            "approved_steps": approved_steps,
            "approvalForm": approvalForm,
            # "generateTokenForm": generateTokenForm,
            "to": to,
        }
    
    def form_valid(self, form):
        role = self.get_form_kwargs().pop("role", None)
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        experience_repo = AppraisalExperienceRepository()
        experience_service_handler = AppraisalExperienceService(appraisal_repo=experience_repo)
        qualifications = UserQualification.objects.filter(user=self.get_object().user)
        context.update(self.approve_form_data())
        context["experience_objects"] = experience_service_handler.get_by_appraisal_id_use_case(appraisal_id=self.get_object().id)
        context["qualification_objects"] = qualifications
        context["appraisal_object"] = self.get_object()
        return context
    
    def get_success_url(self):
        return reverse("update_appraisal", kwargs={"pk": self.kwargs.get("pk")})
    

def approveAppraisal(request,appraisal_id):
    appraisal = Appraisal.objects.get(id=appraisal_id)
    approved_step_object = None 
    
    if request.method == "POST": 
        # generateappraisalform = GenerateappraisalForm(request.POST, request.FILES, instance=appraisal)
        last_approval = appraisal.process.approval_set.last()
        last_step = last_approval.step if last_approval else None
        if (appraisal.process.workflow.step_set.last() is not None and last_step is not None and 
            appraisal.process.workflow.step_set.last().step == ( last_step.step + 1)):
            # if (generateappraisalform.is_valid() and request.FILES.get("appraisal_photo") is not None):
            approved_step_object = approve_step(request, appraisal.process.pk)
            #     print("approved")
            #     # generateappraisalform.save()
            # else:
            #     messages.error(request, "appraisal updloading form is invalid. Have you provided a appraisal photo?", )
        else:
            approved_step_object = approve_step(request, appraisal.process.pk)
    
    # ======= implement return redirect to related view
    return redirect("appraisal_index")

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

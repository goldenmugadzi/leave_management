from typing import Any, Dict, List
from django.urls import reverse
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView, UpdateView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.http import JsonResponse, HttpResponse
from ...models import KeyResultArea, Activity, Appraisal
from ...forms import YearQuarterForm, KraCreateForm
from ...repository.kra import KRARepository
from ...repository.appraisal import AppraisalRepository
from ...services.kra import KRAService
from .helper import build_payload
from ...helpers.getters import get_approved_steps
from datetime import datetime
from pydantic import ValidationError
from approve.forms import ApprovalForm
from approve.models import Step, Approval

from ...helpers.types.kra import KraRolesType
from loguru import logger
class KRACreateView(CreateView):
    """View for creating new Kra"""
    model = KeyResultArea
    form_class = KraCreateForm
    template_name = 'appraisal/kra/create_update.html'
    success_message = 'Key Result Area created successfully'
    context_object_name = "kra_form"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[self.context_object_name] = context.get("form")
        context["appraisal_id"] = self.kwargs.get("appraisal_id")
        return context
    
    def get_appraisal_object(self):
        repo = AppraisalRepository()
        qr = repo.get_appraisal_by_pk(appraisal_id=self.kwargs.get("appraisal_id"))
        
        if qr.exists():
            return qr.first()
        raise Http404("Appraisal not found")
    
    def form_valid(self, form):
        try:
            # Build payload
            payload = build_payload(request=self.request, form=form)
            
            # Call the service to create KRA
            repo = KRARepository()
            service_handler = KRAService(kra_repo=repo)
            kra_object = service_handler.create_use_case(appraisal=self.get_appraisal_object(), data=payload)
            form.instance = kra_object
        except ValidationError:
            # Errors are already handled in build_payload
            return self.form_invalid(form)
        except Exception as e:
            logger.error(f"Failed to create kra with error: {e}")
            messages.error(self.request, f"An unexpected error occurred, please try again")
            return self.form_invalid(form)
        
        # JSON response that inject JavaScript to close the popup and refresh the parent
        js_injector = "<script>opener.refreshKraDropdown(); window.close();</script>"
        return HttpResponse(js_injector)


class KRATemplateView(TemplateView):
    template_name = 'appraisal/kra/index.html'
    
    def get_year_quarter_form(self)->Dict[str, YearQuarterForm]:
        form = YearQuarterForm(self.request.POST or None)
        data = {"year_quarter_form": form}
        return data
    
    def get_all_kra(self, year, quarter)->Dict[str, List[KeyResultArea]]:
        repo = KRARepository()
        service_handler = KRAService(kra_repo=repo)
        kra_queryset = service_handler.fetch_by_quarter_year_appraisal_pk_use_case(year_number=year, quarter_number=quarter, appraisal_id=self.kwargs.get("appraisal_id"))
        data = {"kra_objects": kra_queryset}
        return data
    
    def get_appraisal_object(self):
        year_qrt = self.get_year_quarter()
        kra_queryset = self.get_all_kra(year=year_qrt["year"], quarter=year_qrt["quarter"])["kra_objects"]
        if kra_queryset.exists():
            return kra_queryset.first().appraisal
        raise Http404("No appraisal object found for the given year and quarter.")
    
    def get_approved_steps(self):
        appraisal_object = self.get_appraisal_object()
        result = get_approved_steps(process_object=appraisal_object.process)
        return result
    
    
    def get_year_quarter(self):
        data = {}
        query_param_year = self.request.GET.get('year')
        query_param_quarter = self.request.GET.get('quarter')
        
        if query_param_year is not None or query_param_quarter is not None:
            data["year"] = query_param_year
            data["quarter"] = query_param_quarter
        else:
            current_year = datetime.now().year
            data["year"] = current_year
            data["quarter"] = 1 
        
        return data
    
    
    def approval_user_roles(self)->Dict[str, bool]:
        is_appraiser = self.request.user == self.get_appraisal_object().appraiser
        data = {
            "is_appraiser": is_appraiser
        }
        return data

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context =  super().get_context_data(**kwargs)
        context.update(self.get_year_quarter_form())
        
        year_qrt = self.get_year_quarter()
        
        context.update(self.get_all_kra(year=year_qrt["year"], quarter=year_qrt["quarter"]))
        context.update(year_qrt)
        context.update(self.get_approved_steps())
        context.update(self.approval_user_roles())
        
        context["roles"] = KraRolesType
        context["appraisal_id"] = self.kwargs.get("appraisal_id")
        context["appraisal_object"] = self.get_appraisal_object()
            
        return context
    

class KRAUpdateView(SuccessMessageMixin, UpdateView):
    model = KeyResultArea
    form_class = KraCreateForm
    template_name = 'appraisal/kra/create_update.html'
    success_message = 'Key Result Area updated successfully'
    context_object_name = "kra_form"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[self.context_object_name] = context.get("form")
        return context


    def form_valid(self, form):
        """
            Processes the form when valid, builds a payload, and performs additional actions.
        """
        try:
            payload = build_payload(request=self.request, form=form)
            
            repo = KRARepository()
            service_handler = KRAService(kra_repo=repo)
            
            kra_object = service_handler.update_use_case(kra_object=self.get_object(), quarter_obj=form.cleaned_data.get('quarter'), data=payload)
            form.instance = kra_object
        except ValidationError:
            return self.form_invalid(form)
        except Exception as e:
            messages.error(self.request, f"An unexpected error occurred: {e}")
            return self.form_invalid(form)

        return super().form_valid(form)

    def form_invalid(self, form):
        """
        Handles invalid form submission and adds appropriate messages.
        """
        messages.error(self.request, "There was an error updating the Key Result Area. Please correct the errors below.")
        return super().form_invalid(form)

    def get_success_url(self) -> str:
        """
        Redirects to the index page after successful update.
        """
        kra_obj_id = self.kwargs.get("pk")
        return reverse('kra_update', kwargs={"pk": kra_obj_id})
    
class KRADetailView(TemplateView):
    template_name = "appraisal/kra/detail.html"
    
    def get_object(self):
        obj = get_object_or_404(KeyResultArea, appraisal__id=self.kwargs.get("appraisal_id"))
        return obj
    
    def approve_form_data(self):
        approvalForm = None
        to = None
        completed = False
        
        if not self.get_object().appraisal.process.approval_set.filter(approved="Rejected").exists():  # and allowed:
            try:
                last_approved = self.get_object().appraisal.process.approval_set.last().step.step
            except AttributeError:
                last_approved = 0
            next_step = last_approved + 1
            try:
                newStep = Step.objects.filter(step=next_step, workflow=self.get_object().appraisal.process.workflow)
                
                if newStep.first().approver.name == "appraisee" or newStep.first().approver.name == "appraiser":
                    is_appraisee = newStep.filter(
                        approver__name="appraisee"
                    ).exists()
                    
                    is_appraiser = newStep.filter(
                        approver__name="appraiser"
                    ).exists()
                    if (is_appraisee and self.get_object().appraisal.user == self.request.user) | (is_appraiser and self.get_object().appraisal.appraiser == self.request.user):
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

            completed = self.get_object().appraisal.process.workflow.step_set.last().step == last_approved
        approved_steps = self.get_object().appraisal.process.approval_set.all().values_list(
            "step__step", flat=True
        )
        return {
            "completed": completed,
            "approved_steps": approved_steps,
            "approvalForm": approvalForm,
            # "generateTokenForm": generateTokenForm,
            "to": to,
        }
    
    
    
    
    def get_activities_with_targets(self)->list:
        activities = Activity.objects.filter(kra=self.get_object())
        
        activities_with_targets = []
        for activity in activities:
            targets = Target.objects.filter(activity=activity)
            activities_with_targets.append({
                'activity': activity,
                'targets': targets
            })
        return activities_with_targets
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.approve_form_data())
        context["kra_object"] = self.get_object()
        context["activities_with_targets"] = self.get_activities_with_targets()
        return context
    
    
def kra_list_api(request, appraisal_id):
    """
    API endpoint to retrieve a list of all KRA by their pk.

    Returns:
        JsonResponse
    
    """
    kra = KeyResultArea.objects.filter(appraisal_id__id=appraisal_id).values("id", "name", "created_date").order_by("-created_date")
    return JsonResponse(list(kra), safe=False)

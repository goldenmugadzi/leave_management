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
from datetime import datetime

class KRATemplateView(TemplateView):
    template_name = 'appraisal/kra/index.html'
    
    def get_year_quarter_form(self)->Dict[str, YearQuarterForm]:
        form = YearQuarterForm(self.request.POST or None)
        data = {"year_quarter_form": form}
        return data
    
    def get_all_kra(self, year, quarter)->Dict[str, List[KeyResultArea]]:
        repo = KRARepository()
        service_handler = KRAService(kra_repo=repo)
        kra_queryset = service_handler.get_all_by_quarter_year_use_case(year_number=year, quarter_number=quarter)
        data = {"kra_objects": kra_queryset}
        return data
    
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

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context =  super().get_context_data(**kwargs)
        context.update(self.get_year_quarter_form())
        
        year_qrt = self.get_year_quarter()
        
        context.update(self.get_all_kra(year=year_qrt["year"], quarter=year_qrt["quarter"]))
        context.update(year_qrt)

            
        return context
    

class KRACreateView(SuccessMessageMixin,CreateView):
    model = KeyResultArea
    form_class = KraCreateForm
    template_name = 'appraisal/kra/create_update.html'
    success_message = 'Key Result Area created successfully'
    context_object_name = "kra_form"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[self.context_object_name] = context.get("form")
        return context
    
    def build_payload(self, form) -> KRAType:
        try:
            data = {
                "name": form.cleaned_data.get("name"),
                "description": form.cleaned_data.get("description"),
                "weight": form.cleaned_data.get("weight"),
            }
            return KRAType(**data)
        except ValidationError as e:
            error_message = e.errors()[0]["msg"]
            messages.error(self.request, error_message)
            raise
    
    def form_valid(self, form):
        try:
            # Build payload
            payload = self.build_payload(form)
            
            # Call the service to create KRA
            repo = KRARepository()
            service_handler = KRAService(kra_repo=repo)
            
            kra_object = service_handler.create_use_case(
                quarter_obj=form.cleaned_data.get('quarter'),
                creator_obj=self.request.user,
                data=payload
            )
            form.instance = kra_object
        except ValidationError as e:
            # Errors are already handled in build_payload
            return self.form_invalid(form)
        except Exception as e:
            messages.error(self.request, f"An unexpected error occurred, please try again")
            return self.form_invalid(form)
        
        return super().form_valid(form)
    
    def get_success_url(self) -> str:
        return reverse('kra_index')
    
    
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
    
    def build_payload(self, form) -> KRAType:
        """
        Constructs and validates a KRAType payload from the form data.
        """
        try:
            data = {
                "name": form.cleaned_data.get("name"),
                "description": form.cleaned_data.get("description"),
                "weight": form.cleaned_data.get("weight"),
            }
            return KRAType(**data)
        except ValidationError as e:
            error_message = e.errors()[0]["msg"]
            messages.error(self.request, error_message)
            raise

    def form_valid(self, form):
        """
        Processes the form when valid, builds a payload, and performs additional actions.
        """
        try:
            payload = self.build_payload(form)
            
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
    
from typing import Any, Dict, List
from django.urls import reverse, reverse_lazy
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView, UpdateView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from ...models import KeyResultArea, AppraisalKra
from ...forms import KraCreateForm
from ...repository.kra import KRARepository, TargetScoreRepository, KRAOutComeRepository
from ...services.kra import KRAService
from .helper import PayloadDeserializationStrategyContext, KraDeserializationStrategy
from pydantic import ValidationError

from loguru import logger


class KRACreateView(CreateView):
    """View for creating new Kra"""
    model = KeyResultArea
    form_class = KraCreateForm
    template_name = 'appraisal/kra/create_update.html'
    success_message = 'Key Result Area created successfully'
    context_object_name = "kra_form"
    success_url = reverse_lazy('kra_index')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[self.context_object_name] = context.get("form")
        return context

    def form_valid(self, form):
        try:
            # Build payload
            payload_deserialize_strategy = PayloadDeserializationStrategyContext(strategy=KraDeserializationStrategy())
            payload = payload_deserialize_strategy.deserialize_payload(request_object=self.request, form_object=form)
            
            # Call the service to create KRA
            repo = KRARepository()
            kra_object = repo.create(creator=self.request.user, data=payload)
            
            if kra_object is None:
                messages.error(self.request, "KRA with this description already exists")
                return super().form_invalid(form)
            form.instance = kra_object
        except ValidationError:
            # Errors are already handled in build_payload
            return super().form_invalid(form)
        except Exception as e:
            logger.error(f"Failed to create kra with error: {e}")
            messages.error(self.request, f"An unexpected error occurred, please try again")
            return super().form_invalid(form)
        return super().form_valid(form)


class KRATemplateView(TemplateView):
    template_name = 'appraisal/kra/index.html'
    
    def get_all_kra(self)->Dict[str, List[KeyResultArea]]:
        repo = KRARepository()
        kra_queryset = repo.fetch_all()
        data = {"kra_objects": kra_queryset}
        return data

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context =  super().get_context_data(**kwargs)
        context.update(self.get_all_kra())        
        return context

class KRAUpdateView(SuccessMessageMixin, UpdateView):
    model = KeyResultArea
    form_class = KraCreateForm
    template_name = 'appraisal/kra/create_update.html'
    success_message = 'Key Result Area updated successfully'
    context_object_name = "kra_form"
    
    def get_object(self, queryset=None):
        
        return super().get_object(queryset)
    
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
        obj = get_object_or_404(AppraisalKra, pk=self.kwargs.get("appraisal_kra_id"))
        return obj
    
    def get_score_objects(self)->List[TargetScoreRepository]:
        score_repo = TargetScoreRepository()
        return score_repo.fetch_by_appraisal_kra_id(appraisal_kra_id=self.kwargs.get("appraisal_kra_id"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["score_objects"] = self.get_score_objects()
        context["kra_object"] = self.get_object()
        return context
    
    def get(self, request, *args, **kwargs):
        try:
            self.get_score_objects()
        except Exception as e:
            logger.error(f"KRADetailView for appraisal_kra_id: {self.kwargs.get('appraisal_kra_id')}, failed with error: {e}")
            return redirect("server_error_view")
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)
   

class KRAOutComeTemplateView(TemplateView):
    template_name = 'appraisal/kra/outcomes/index.html'
    
    def get_all_kra_outcomes(self)->Dict[str, List[KeyResultArea]]:
        repo = KRAOutComeRepository()
        kra_outcomes_queryset = repo.fetch_by_kra_id(kra_id=self.kwargs.get("kra_id"))
        data = {"kra_outcomes_objects": kra_outcomes_queryset}
        return data
    
    def get_kra_obj(self):
        repo = KRARepository()
        return repo.retrieve_by_id(kra_id=self.kwargs.get("kra_id"))
        
        
    
    def get(self, request, *args, **kwargs):
        try:
            self.object = self.get_kra_obj()
            if self.object is None:
                logger.error(f"KRAOutComeTemplateView view failed with no kra object fount, pk-{self.kwargs.get('kra_id')}")
                return redirect("server_error_view")
            context = self.get_context_data(**kwargs)
            return self.render_to_response(context)
        except Exception as e:
            logger.error(f"KRAOutComeTemplateView view with kra pk-{self.kwargs.get('kra_id')}, failed with error: {e}")
            return redirect("server_error_view")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context =  super().get_context_data(**kwargs)
        context.update(self.get_all_kra_outcomes())        
        return context

 
def kra_list_api(request, appraisal_id):
    """
    API endpoint to retrieve a list of all KRA by their pk.

    Returns:
        JsonResponse
    
    """
    appraisal_service_handler = KRAService(kra_repo=KRARepository())
    appraisal_object = appraisal_service_handler.get_kra_by_pk_use_case(kra_id=appraisal_id)
    kra = KeyResultArea.objects.filter(designation__id=appraisal_object.user.designation.id).values("id", "name", "created_date").order_by("-created_date")
    return JsonResponse(list(kra), safe=False)

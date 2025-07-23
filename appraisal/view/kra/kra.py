from typing import Any, Dict, List
from django.urls import reverse, reverse_lazy
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView, UpdateView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from ...models import KeyResultArea, KeyResultAreaOutCome
from ...forms import KraCreateForm, KraOutComeCreateForm
from ...repository.kra import KRARepository, KRAOutComeRepository
from ...services.kra import KRAService
from ..helper import PayloadDeserializationStrategyContext, KraDeserializationStrategy, KraOutComeDeserializationStrategy
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
        context["is_create"] = True
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

class KRAUpdateDetailView(SuccessMessageMixin, UpdateView):
    model = KeyResultArea
    form_class = KraCreateForm
    template_name = 'appraisal/kra/create_update.html'
    success_message = 'Key Result Area updated successfully'
    context_object_name = "kra_form"
    
    def get_object(self, queryset=None):
        repo = KRARepository()
        return repo.retrieve_by_id(kra_id=self.kwargs.get("kra_id"))
    
    def get_kra_outcome_form(self, post_request=None):
        if post_request is None:
            return KraOutComeCreateForm()
        return KraOutComeCreateForm(post_request)

    def get_all_kra_outcomes(self):
        repo = KRAOutComeRepository()
        return repo.fetch_by_kra_id(kra_id=self.kwargs.get("kra_id"))
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[self.context_object_name] = context.get("form")
        context["kra_outcome_form"] = self.get_kra_outcome_form()
        context["kra_outcomes_qr"] = self.get_all_kra_outcomes()
        context["is_create"] = False
        return context
    
    def handle_kra_form_update(self, form):
        # Build payload
        payload_deserialize_strategy = PayloadDeserializationStrategyContext(strategy=KraDeserializationStrategy())
        payload = payload_deserialize_strategy.deserialize_payload(request_object=self.request, form_object=form)
        
        # Call the service to create KRA
        repo = KRARepository()
        return repo.update(kra_object=self.get_object(), data=payload, updated_by=self.request.user)

    def handle_kra_outcome_form_update(self, form):
         # Build payload
        payload_deserialize_strategy = PayloadDeserializationStrategyContext(strategy=KraOutComeDeserializationStrategy())
        payload = payload_deserialize_strategy.deserialize_payload(request_object=self.request, form_object=form)

        repo = KRAOutComeRepository()
        kra_outcome_obj = repo.create(outcome_description=payload.outcome_description,
                           kra_obj=self.get_object()
                           )
        messages.success(request=self.request, message="Outcome successfully created.")
        return kra_outcome_obj
    
    def is_kra_request_form(self)->bool:
        """Handler that checks if the POST request is from kra form or kra outcome form

        Returns:
            bool: True if kra form and False if kra outcome
        """
        if "kra_request" in self.request.POST:
            return True
        return False
    
    
    def post(self, request, *args, **kwargs):
        """
            Handle POST requests: instantiate a form instance with the passed
            POST variables and then check if it's valid.
        """
        self.object = self.get_object() 
        
        if self.is_kra_request_form():
            form = self.get_form()
        else:
            form = self.get_kra_outcome_form(request.POST)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        """
            Processes the form when valid, builds a payload, and performs additional actions.
        """
        try:
            if self.is_kra_request_form():
                object = self.handle_kra_form_update(form=form)
            else:
                object = self.handle_kra_outcome_form_update(form=form)
            form.instance = object
        except ValidationError:
            # Errors are already handled in build_payload
            return super().form_invalid(form)
        except Exception as e:
            messages.error(self.request, f"An unexpected error occurred: {e}")
            return super().form_invalid(form)

        return super().form_valid(form)

    def get(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
            self.get_all_kra_outcomes()
            if self.object is None:
                logger.warning(f"KRAUpdateDetailView for kra_id: {self.kwargs.get('kra_id')}, doesn`t exists")
                return redirect("server_error_view")
        except Exception as e:
            logger.error(f"KRAUpdateDetailView for kra_id: {self.kwargs.get('kra_id')}, failed with error: {e}")
            return redirect("server_error_view")
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def get_success_url(self) -> str:
        """
        Redirects to the index page after successful update.
        """
        kra_obj_id = self.kwargs.get("kra_id")
        return reverse('kra_update_detail', kwargs={"kra_id": kra_obj_id})
    

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
    
class KRAOutComeUpdateView(CreateView):
    """View for creating new Kra"""
    model = KeyResultAreaOutCome
    form_class = KraOutComeCreateForm
    template_name = 'appraisal/kra/outcomes/create_update.html'
    success_message = 'OutCome created successfully'
    context_object_name = "kra_outcome_form"
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

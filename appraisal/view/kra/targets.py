from typing import Dict
from django.urls import reverse
from django.shortcuts import redirect
from django.forms.models import model_to_dict
from django.views.generic.edit import UpdateView, CreateView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.http import Http404, HttpResponseServerError
from django.http.response import HttpResponseRedirect
from django.http import JsonResponse
from django.template.loader import render_to_string

from ...models import TargetScore, ScoreDocument
from ...forms import ScoreDocumentForm, TargetScoreForm

from ...repository.kra import TargetScoreRepository, ScoreDocumentRepository
from ...services.kra import TargetScoreService
from ...helpers.setters import set_approval_process

from ..helper import build_payload_score
from pydantic import ValidationError
from loguru import logger


class TargetScoreUpdateView(SuccessMessageMixin, UpdateView):
    model = TargetScore
    form_class = TargetScoreForm
    template_name = 'appraisal/kra/targets/score_form.html'
    success_message = 'Scoring was set successfully'
    context_object_name = "target_score_form"

    def get_target_score_object(self):
        repo = TargetScoreRepository()
        performance_dimension_id = self.kwargs.get("performance_dimension_id")
        return repo.get_by_performance_dimension_id(performance_dimension_id=performance_dimension_id)

    def get_object(self, queryset=None):
        """
        Override the default get_object method to retrieve the performance_dimension object using a custom service.
        """
        obj = self.get_target_score_object()
        return obj
    
    def get_score_documents(self):
        repo = ScoreDocumentRepository()
        qr = repo.fetch_by_score_id(score_id=self.get_object().id)
        return {"score_documents_qr": qr}
    
    def get(self, request, *args, **kwargs):
        try:
            score_object = self.get_object()
            self.object = score_object
            if score_object is None:
                logger.error(f"Update view for TargetScore with performance_dimension pk-{self.kwargs.get('performance_dimension_id')}, Score object not found")
                return redirect("server_error_view")
            context = self.get_context_data(**kwargs)
            return self.render_to_response(context)
        except Exception as e:
            logger.error(f"Update view for TargetScore with performance_dimension pk-{self.kwargs.get('performance_dimension_id')}, failed with error: {e}")
            return redirect("server_error_view")
        
    def approval_user_roles(self)->Dict[str, bool]:
        appraisal_object = self.get_object().performance_dimension.activity.appraisal_kra.appraisal
        is_appraiser = self.request.user == appraisal_object.appraiser
        is_appraisee = self.request.user == appraisal_object.user
        
        data = {
            "is_appraiser": is_appraiser,
            "is_appraisee": is_appraisee
        }
        return data
    
    def get_initial_form(self):
        return TargetScoreForm(instance=self.get_object())
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[self.context_object_name] = self.get_initial_form()
        
        context.update(self.get_score_documents())
        context.update(self.approval_user_roles())
        context["target_score_object"] = self.get_target_score_object()
        return context

    def form_valid(self, form):
        try:
            if "appraisee_request" in self.request.POST:
                payload = build_payload_score(request=self.request, form=form, is_appraisee=True)
            elif "appraiser_request" in self.request.POST:
                payload = build_payload_score(request=self.request, form=form, is_appraisee=False)
            else:
                raise Exception("Request not allowed, only 'appraisee_request' and 'appraiser_request' allowed")
            
            repo = TargetScoreRepository()
            service_handler = TargetScoreService(target_score_repository=repo)
            target_score_object = service_handler.update_use_case(target_score_obj=self.get_object(), data=payload)

            form.instance = target_score_object
        except ValidationError:
            return super().form_invalid(form)
        except Exception as e:
            logger.error(f"[ TargetScoreUpdateView ] for target score pk: {self.get_object().id}, failed with error: {e}")
            messages.error(self.request, "An unexpected error occurred, please try again")
            return super().form_invalid(form)
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """
        Redirects to the index page after successful update.
        """
        return reverse('score_view', kwargs={"performance_dimension_id": self.kwargs.get('performance_dimension_id')})

class ScoreDocumentCreateView(SuccessMessageMixin, CreateView):
    model = ScoreDocument
    form_class = ScoreDocumentForm
    template_name = 'appraisal/kra/targets/score_docs/create_update.html'
    success_message = 'Supporting document was set successfully'
    context_object_name = "score_document_form"

    def get_target_score_object(self):
        repo = TargetScoreRepository()
        score_id = self.kwargs.get("target_score_id")
        try:
            obj = repo.get_by_id(score_id=score_id)
            if obj is None:
                raise Http404("Score object not found") 
            return obj
        except Exception as e:
            logger.error(f"[ScoreDocumentCreateView] with score obj pk - {score_id}, failed with error: {e}")
            return HttpResponseServerError("Something went wrong, please try again.")

    def get(self, request, *args, **kwargs):
        self.object = None
        self.get_target_score_object()
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_create"] = True
        context[self.context_object_name] = context.get("form")
        return context

    def form_valid(self, form):
        try:
            file_name = form.cleaned_data.get('name')
            file_obj = self.request.FILES.get('documents')
            repo = ScoreDocumentRepository()
            score_doc_obj = repo.create(score_obj=self.get_target_score_object(), name=file_name, file=file_obj)
 
            form.instance = score_doc_obj
        except ValidationError:
            return super().form_invalid(form)
        except Exception as e:
            logger.error(f"[ScoreDocumentCreateView] form_valid, failed with error: {e}")
            messages.error(self.request, f"something went wrong, please try again")
            return super().form_invalid(form)
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """
        Redirects to the index page after successful update.
        """
        return reverse('score_view', kwargs={"performance_dimension_id": self.kwargs.get('performance_dimension_id')})

class ScoreDocumentUpdateView(SuccessMessageMixin, UpdateView):
    model = ScoreDocument
    form_class = ScoreDocumentForm
    template_name = 'appraisal/kra/targets/score_docs/create_update.html'
    success_message = 'Supporting document was set successfully'
    context_object_name = "score_document_form"

    def get_target_score_object(self):
        repo = TargetScoreRepository()
        score_id = self.kwargs.get("target_score_id")
        try:
            obj = repo.get_by_id(score_id=score_id)
            if obj is None:
                raise Http404("Score object not found") 
            return obj
        except Exception as e:
            logger.error(f"[ScoreDocumentUpdateView] with score obj pk - {score_id}, failed with error: {e}")
            return HttpResponseServerError("Something went wrong, please try again.")

    def get_score_doc_object(self):
        repo = ScoreDocumentRepository()
        score_doc_id = self.kwargs.get("score_doc_id")
        try:
            obj = repo.get_by_id(score_doc_id=score_doc_id)
            if obj is None:
                raise Http404("Score supporting document object not found") 
            return obj
        except Exception as e:
            logger.error(f"[ScoreDocumentUpdateView] with score doc obj pk - {score_doc_id}, failed with error: {e}")
            return HttpResponseServerError("Something went wrong, please try again.")
    
    def get_object(self, queryset = ...):
        return self.get_score_doc_object()
    
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.get_target_score_object()
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_create"] = False
        context[self.context_object_name] = context.get("form")
        return context

    def form_valid(self, form):
        try:
            file_name = form.cleaned_data.get('name')
            file_obj = self.request.FILES.get('documents')
            repo = ScoreDocumentRepository()
            score_doc_obj = repo.update(score_doc_obj=self.get_object(), name=file_name, file=file_obj)
 
            form.instance = score_doc_obj
        except ValidationError:
            return super().form_invalid(form)
        except Exception as e:
            logger.error(f"[ScoreDocumentUpdateView] form_valid, failed with error: {e}")
            messages.error(self.request, f"something went wrong, please try again")
            return super().form_invalid(form)
        return super().form_valid(form)
    
    def post(self, request, *args, **kwargs):
        """
        Handle POST requests: instantiate a form instance with the passed
        POST variables and then check if it's valid.
        """
        if "delete_request" in self.request.POST:
            repo = ScoreDocumentRepository()
            try:
                repo.delete_obj(score_doc_obj=self.get_object())
                messages.success(self.request, "Supporting document deleted successfully")
            except Exception as e:
                logger.error(f"[ScoreDocumentUpdateView] deletion request failed with error: {e}")
                messages.error(self.request, "Supporting document deletion failed, please try again")
            
                
            return HttpResponseRedirect(self.get_success_url())
        
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_success_url(self) -> str:
        """
        Redirects to the index page after successful update.
        """
        return reverse('score_view', kwargs={"performance_dimension_id": self.kwargs.get('performance_dimension_id')})


    
def target_score_supporting_docs_view(request, performance_dimension_pk: int):
    target_score_object = TargetScoreRepository().get_by_performance_dimension_id(performance_dimension_id=performance_dimension_pk)
    
    if target_score_object is None:
        return HttpResponseServerError("Something went wrong")
    
    performance_dimension_obj = target_score_object.performance_dimension
    score_doc_repo = ScoreDocumentRepository()
    
    try:
        score_documents_qr = score_doc_repo.fetch_by_score_id(score_id=target_score_object.id)
    except Exception as e:
        logger.error(f"[target_score_supporting_docs_view] with performance_dimension pk: {performance_dimension_pk}, on fetching score docs failed with error: {e}")
    
    # Render the inner HTML
    content_html = render_to_string(
        "appraisal/kra/targets/score_docs/index.html",
        {
            "target_score_object": target_score_object,
            "score_documents_qr": score_documents_qr,
        },
        request=request
    )

    return JsonResponse({
        "heading": performance_dimension_obj.performance_indicator,
        "description": performance_dimension_obj.description,
        "content": content_html
    })
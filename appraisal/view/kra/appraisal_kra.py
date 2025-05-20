from typing import Any, Dict, List
from django.urls import reverse
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView, UpdateView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.http import Http404
from ...models import KeyResultArea, AppraisalKra, Appraisal, TargetScore
from ...forms import YearQuarterForm, AppraisalKraForm
from ...repository.kra import AppraisalKraRepository
from ...repository.appraisal import AppraisalRepository
from ...services.kra import AppraisalKraService, ActivityService
from ...repository.kra import KraActivityRepository, PerformanceDimensionRepository
from ...repository import AppraisalRepository, TargetScoreRepository
from datetime import datetime
from ...helpers.types.kra import KraRolesType
from ...helpers.getters.approval import ApprovalStagesHandler
from loguru import logger


class AppraisalKraTemplateView(TemplateView):
    template_name = 'appraisal/kra/appraisal_kra/index.html'
    
    def get_year_quarter_form(self)->Dict[str, YearQuarterForm]:
        form = YearQuarterForm(self.request.POST or None)
        data = {"year_quarter_form": form}
        return data
    
    def get_all_kra(self, year, quarter)->Dict[str, List[AppraisalKra]]:
        repo = AppraisalKraRepository()
        service_handler = AppraisalKraService(repo=repo)
        queryset = service_handler.fetch_by_quarter_year_appraisal_pk_use_case(year_number=year, quarter_number=quarter, appraisal_id=self.kwargs.get("appraisal_id"))
        data = {"appraisal_kra_objects": queryset}
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
    
    def get_appraisal_object(self):
        try:
            qr = AppraisalRepository().get_appraisal_by_pk(appraisal_id=self.kwargs.get("appraisal_id"))
        
            if qr.exists():
                return qr.first()
            raise Http404("Appraisal not found")
        except Exception as e:
            logger.error(f"Get appraisal by pk failed with error: {e}")
        
        
    def appraiser_role(self):
        is_appraiser = self.request.user == self.get_appraisal_object().appraiser
        data = {
            "is_appraiser": is_appraiser
        }
        return data

    def get_approval_stages(self):
        try:
            handler = ApprovalStagesHandler(appraisal_id=self.get_appraisal_object().id)
            return handler.get_stages_info()
        except Exception as e:
            logger.error(f"[PerformancePlanAndAssessmentTemplateView] for Appraisal - {self.get_appraisal_object()} failed with error: {e}")
            return None
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context =  super().get_context_data(**kwargs)
        context.update(self.get_year_quarter_form())
        
        year_qrt = self.get_year_quarter()
        
        context.update(self.get_all_kra(year=year_qrt["year"], quarter=year_qrt["quarter"]))
        context.update(year_qrt)
        context.update(self.appraiser_role())
        context.update(self.get_approval_stages())
        
        context["roles"] = KraRolesType
        context["appraisal_id"] = self.kwargs.get("appraisal_id")
            
        return context
    
    def get(self, request, *args, **kwargs):
        approval_data = self.get_approval_stages()
        if approval_data is None:
            return redirect("server_error_view")
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)
    
        

class AppraisalKraCreateView(SuccessMessageMixin, CreateView):
    model = AppraisalKra
    form_class = AppraisalKraForm
    template_name = 'appraisal/kra/appraisal_kra/create_update.html'
    success_message = 'Key Result Area created successfully'
    context_object_name = "appraisal_kra_form"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["appraisee_id"] = self.get_appraisal_object().user.id
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[self.context_object_name] = context.get("form")
        context["appraisal_id"] = self.kwargs.get("appraisal_id")
        return context
    
    def get_appraisal_object(self):
        qr = AppraisalRepository().get_appraisal_by_pk(appraisal_id=self.kwargs.get("appraisal_id"))
        if qr.exists():
            return qr.first()
        return Http404("Appraisal not found")
    
    def post(self, request, *args, **kwargs):
        """
        Handle POST requests: instantiate a form instance with the passed
        POST variables and then check if it's valid.
        """
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)
        
    def form_invalid(self, form):
        self.object = None  
        messages.error(self.request, "A Key Result Area (KRA) or a Supervisor Activity is required. Please provide at least one to proceed.")
        return self.render_to_response(self.get_context_data(form=form))
    
    def form_valid(self, form):
        kra_obj = form.cleaned_data.get("new_kra")
        assigned_kra_obj = form.cleaned_data.get("assigned_kra")
        
        if (kra_obj is None and assigned_kra_obj is None) or (kra_obj is not None and assigned_kra_obj is not None):
            return self.form_invalid(form)
        
        quarter_year_obj = form.cleaned_data.get("quarter")
        try:
            appraisal_kra_object = AppraisalKraRepository().create(appraisal_object=self.get_appraisal_object(), quarter_obj=quarter_year_obj, kra_obj=kra_obj, activity_object=assigned_kra_obj)
            form.instance = appraisal_kra_object
        except Exception as e:
            logger.error(f"Failed to create appraisal kra: {e}")
            messages.error(self.request, "Something went wrong, please try again")
        
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('appraisal_kra_index', kwargs={"appraisal_id": self.kwargs.get("appraisal_id")})
    

class AppraisalKraUpdateView(SuccessMessageMixin, UpdateView):
    model = AppraisalKra
    form_class = AppraisalKraForm
    template_name = 'appraisal/kra/appraisal_kra/create_update.html'
    success_message = 'Key Result Area created successfully'
    context_object_name = "appraisal_kra_form"
    
    def get_object(self, queryset = ...):
        repo = AppraisalKraRepository()
        obj = repo.retrieve_by_pk(pk=self.kwargs.get("appraisal_kra_id"))
        return obj
    
    
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[self.context_object_name] = context.get("form")
        context["appraisal_id"] = self.get_object().appraisal.id
        return context
    
    def form_invalid(self, form):
        messages.error(self.request, "A Key Result Area (KRA) or a Supervisor Activity is required. Please provide at least one to proceed.")
        return self.render_to_response(self.get_context_data(form=form))
    

    def form_valid(self, form):
        """
            Processes the form when valid, builds a payload, and performs additional actions.
        """
        kra_obj = form.cleaned_data.get("new_kra")
        assigned_kra_obj = form.cleaned_data.get("assigned_kra")
        
        if (kra_obj is None and assigned_kra_obj is None) or (kra_obj is not None and assigned_kra_obj is not None):
            return self.form_invalid(form)
        
        quarter_year_obj = form.cleaned_data.get("quarter")
        try:
            appraisal_kra_object = AppraisalKraRepository().update(appraisal_kra_obj=self.get_object(), quarter_obj=quarter_year_obj, kra_obj=kra_obj, activity_object=assigned_kra_obj)
            form.instance = appraisal_kra_object
        except Exception as e:
            logger.error(f"Failed to create appraisal kra: {e}")
            messages.error(self.request, "Something went wrong, please try again")
        
        return super().form_valid(form)


    def get_success_url(self) -> str:
        """
        Redirects to the index page after successful update.
        """
        kra_obj_id = self.kwargs.get("appraisal_kra_id")
        return reverse('appraisal_kra_update', kwargs={"appraisal_kra_id": kra_obj_id})


class AppraisalKraDetailView(TemplateView):
    template_name = "appraisal/kra/appraisal_kra/detail.html"
    
    def get_object(self):
        obj = get_object_or_404(AppraisalKra, pk=self.kwargs.get("appraisal_kra_id"))
        return obj
    
    def get_approval_stages(self):
        try:
            handler = ApprovalStagesHandler(appraisal_id=self.get_object().appraisal.id)
            return handler.get_stages_info()
        except Exception as e:
            logger.error(f"[AppraisalKraDetailView] for Appraisal - {self.get_object().appraisal} failed with error: {e}")
            return None
    
    def get_score_objects(self)->List[TargetScore]:
        score_repo = TargetScoreRepository()
        return score_repo.fetch_by_appraisal_kra_id(appraisal_kra_id=self.kwargs.get("appraisal_kra_id"))

    def get_activities_related_data(self)->List[Dict]:
        try:
            service_handler = ActivityService(activity_repo=KraActivityRepository())
            data = service_handler.get_activities_related_data_by_appraisal_kra_id(appraisal_kra_id=self.kwargs.get("appraisal_kra_id"), performance_dimension_repo=PerformanceDimensionRepository())
            return data
        except Exception as e:
            logger.error(f"[AppraisalKraDetailView] get_activities_related_data for Appraisal - {self.get_object().appraisal} failed with error: {e}")
            return None
    
    def is_reviewer(self)->bool:
        return self.request.user == self.get_object().appraisal.reviewer
    
    def appraisal_kra_activities_scored(self)->bool:
        score_repo = TargetScoreRepository()
        return score_repo.appraisal_kra_activities_scored(appraisal_kra_id=self.kwargs.get("appraisal_kra_id"))

    def get_supporting_docs_api_url(self):
        url = f"{{ request.scheme }}://{{ request.get_host }}"
        return url
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_approval_stages())
        context["activities_data"] = self.get_activities_related_data()
        context["appraisal_kra_object"] = self.get_object()
        context["is_reviewer"] = self.is_reviewer()   
        context["appraisal_kra_activities_scored"] = self.appraisal_kra_activities_scored()
        context["score_doc_api_url"] = self.get_supporting_docs_api_url()
        return context
    
    def get(self, request, *args, **kwargs):
        try:
            self.get_score_objects()
            self.is_reviewer()
            self.appraisal_kra_activities_scored()
        except Exception as e:
            logger.error(f"AppraisalKraDetailView for appraisal_kra_id: {self.kwargs.get('appraisal_kra_id')}, failed with error: {e}")
            return redirect("server_error_view")
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)
from typing import Any, Dict, List
from django.urls import reverse
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView, UpdateView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.http import Http404
from ...models import KeyResultArea, AppraisalKra, Appraisal
from ...forms import YearQuarterForm, AppraisalKraForm
from ...repository.kra import AppraisalKraRepository
from ...services.kra import AppraisalKraService
from ...helpers.getters import get_approved_steps
from ...repository import UserQualificationRepository, AppraisalExperienceRepository, ExperienceRepository, AppraisalRepository
from ...services import AppraisalService
from datetime import datetime
from ...helpers.types.kra import KraRolesType
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

    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context =  super().get_context_data(**kwargs)
        context.update(self.get_year_quarter_form())
        
        year_qrt = self.get_year_quarter()
        
        context.update(self.get_all_kra(year=year_qrt["year"], quarter=year_qrt["quarter"]))
        context.update(year_qrt)
        context.update(self.appraiser_role())
        context["roles"] = KraRolesType
        context["appraisal_id"] = self.kwargs.get("appraisal_id")
            
        return context


class AppraisalKraCreateView(SuccessMessageMixin, CreateView):
    model = AppraisalKra
    form_class = AppraisalKraForm
    template_name = 'appraisal/kra/appraisal_kra/create_update.html'
    success_message = 'Key Result Area created successfully'
    context_object_name = "appraisal_kra_form"
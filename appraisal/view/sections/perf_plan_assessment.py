from typing import Any, Dict, List
from django.forms import BaseModelForm
from django.http import HttpResponse
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic import TemplateView
from django.urls import reverse, reverse_lazy
from django.utils.text import slugify

from django.shortcuts import redirect, render
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages

from ...repository.appraisal import AppraisalRepository
from ...repository.kra import AppraisalDepartmentOutputRepository, AppraisalOutPutPerformanceDimensionScoreRepository
from ...services.kra import AppraisalDepartmentOutputService
from it.users.models import GRADE_CHOICES
from loguru import logger


class AppraisalDepartmentOutputTemplateView(TemplateView):
    template_name = 'appraisal/performance_plan/appraisal_department_output.html'
    
    def get_appraisal_object(self):
        repo = AppraisalRepository()
        return repo.get_appraisal_by_pk(appraisal_id=self.kwargs.get('appraisal_id'))
    
    def get_all_appraisal_dept_output_quarters(self):
        appraisal_object = self.get_appraisal_object()
        appraisal_year = appraisal_object.created_date.year
        service_handler = AppraisalDepartmentOutputService(appraisal_department_output_repo=AppraisalDepartmentOutputRepository())
        return service_handler.fetch_quarterly(appraisal_id=appraisal_object.id, year=appraisal_year) 
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        appraisee_object = self.get_appraisal_object().user
        context["appraisal_dept_output_qr"] = self.get_all_appraisal_dept_output_quarters()
        context["appraisee_object"] = appraisee_object
        context["is_grade_c_and_above"] = appraisee_object.grade == GRADE_CHOICES[2][0]
        return context
    
    def get(self, request, *args, **kwargs):
        try:
            appraisal_id = self.kwargs.get('appraisal_id')
            appraisal_object = self.get_appraisal_object()
            if appraisal_object is None:
                logger.warning(f"[AppraisalDepartmentOutputTemplateView] get_appraisal_object() with appraisal pk: {appraisal_id}, not found error")
                return redirect("object_not_found_error", object_name=slugify("Appraisal"))

        except Exception as e:
            logger.error(f"[AppraisalDepartmentOutputTemplateView]  get_appraisal_object() with appraisal pk: {appraisal_id}, failed with error: {e}")
            return redirect("server_error_view")
        return super().get(request, *args, **kwargs)

class AppraisalDepartmentPerformanceDimensionTemplateView(TemplateView):
    template_name = 'appraisal/performance_plan/appraisal_department_perf_dimension.html'

    def get_appraisal_department_output_obj(self):
        repo = AppraisalDepartmentOutputRepository()
        return repo.get_by_id(appraisal_department_output_id=self.kwargs.get('appraisal_department_output_id'))

    def get_appraisee_object(self):
        dept_appraisal_output_obj = self.get_appraisal_department_output_obj()
        return dept_appraisal_output_obj.appraisal.user
    
    def get_all_perf_dimensions(self):
        repo = AppraisalOutPutPerformanceDimensionScoreRepository()
        return repo.fetch_by_department_output_id(appraisal_department_output_id=self.kwargs.get('appraisal_department_output_id'))
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        appraisee_object = self.get_appraisee_object()
        context["appraisee_object"] = appraisee_object
        context["department_output_obj"] = self.get_appraisal_department_output_obj().department_output
        context["is_grade_c_and_above"] = appraisee_object.grade == GRADE_CHOICES[2][0]
        context["performance_dimensions_qr"] = self.get_all_perf_dimensions()
        return context
    
    
    def get(self, request, *args, **kwargs):
        try:
            appraisal_department_output_id = self.kwargs.get('appraisal_department_output_id')
            appraisal_department_output_obj = self.get_appraisal_department_output_obj()
            if appraisal_department_output_obj is None:
                logger.warning(f"[AppraisalDepartmentOutputTemplateView] get_appraisal_department_output_obj() with appraisal_department_output pk: {appraisal_department_output_id}, not found error")
                return redirect("object_not_found_error", object_name=slugify("Department Output"))

        except Exception as e:
            logger.error(f"[AppraisalDepartmentOutputTemplateView]  get_appraisal_department_output_obj() with appraisal_department_output pk: {appraisal_department_output_id}, failed with error: {e}")
            return redirect("server_error_view")
        return super().get(request, *args, **kwargs)
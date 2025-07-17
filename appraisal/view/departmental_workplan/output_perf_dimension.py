from typing import Any, Dict, List
from django.forms import BaseModelForm
from django.http import HttpResponse
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic import TemplateView
from django.urls import reverse
from django.utils.text import slugify
from django.shortcuts import redirect

from ...repository.departmental_workplan import DepartmentalOutRepository, OutPutPerformanceDimensionRepository
from ...services.department_workplan import OutPutPerformanceDimensionService
from ...models.departmental_workplan import DepartmentOutput
from loguru import logger

def get_perf_dimension_weight_progress(department_output_obj: DepartmentOutput):
    handler = OutPutPerformanceDimensionService(repo=OutPutPerformanceDimensionRepository())
    return handler.get_outputs_weight_progress(department_output_obj=department_output_obj)

class OutPutPerformanceDimensionTemplateView(TemplateView):
    template_name = 'appraisal/departmental_workplan/outputs/performance_dimension/index.html'
    
    def get_department_output_obj(self):
        repo = DepartmentalOutRepository()
        return repo.get_by_id(dept_output_id=self.kwargs.get("department_output_id"))
    
    def get_weight_progress(self):
        return get_perf_dimension_weight_progress(department_output_obj=self.get_department_output_obj())
    
    def get_all_output_dimension(self):
        repo = OutPutPerformanceDimensionRepository()
        return repo.fetch_by_department_output_id(department_output_id=self.kwargs.get('department_output_id'))
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        dept_output_progress_data = {
            "weight": self.get_department_output_obj().weight,
            "covered_weight": self.get_weight_progress().covered_weight,
            "remain_weight": self.get_weight_progress().remaining_weight
        }
        context.update(**dept_output_progress_data)
        context["department_out_obj"] = self.get_department_output_obj()
        context["performance_dimensions_qr"] = self.get_all_output_dimension()
        return context
    
    def get(self, request, *args, **kwargs):
        self.object = None
        try:
            self.get_weight_progress()
            departmental_output_obj = self.get_department_output_obj()
            if departmental_output_obj is None:
                logger.warning(f"[DepartmentOutputTemplateView] get_department_output_obj() with pk: {self.kwargs.get('department_output_id')}, not found error")
                return redirect("object_not_found_error", object_name=slugify("Departmental output"))
            
            if not self.get_all_output_dimension().exists():
                logger.warning(f"[DepartmentOutputTemplateView] get_all_output_dimension() with departmental output pk: {self.kwargs.get('department_output_id')}, not found error")
                return redirect("object_not_found_error", object_name=slugify("Output Performance Dimensions"))
            
        except Exception as e:
            logger.error(f"[DepartmentOutputTemplateView] get_department_output_obj() with  pk: {self.kwargs.get('department_output_id')}, failed with error: {e}")
            return redirect("server_error_view")
        return super().get(request, *args, **kwargs) 
    
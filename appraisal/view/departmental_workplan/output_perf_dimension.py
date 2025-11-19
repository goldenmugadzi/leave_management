from typing import Any, Dict, List
from django.forms import BaseModelForm
from django.http import HttpResponse
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic import TemplateView
from django.urls import reverse
from django.utils.text import slugify
from django.shortcuts import redirect
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages

from ...repository.departmental_workplan import DepartmentalOutRepository, OutPutPerformanceDimensionRepository
from ...services.department_workplan import OutPutPerformanceDimensionService
from ...models.departmental_workplan import DepartmentOutput, OutPutPerformanceDimension, PERFORMANCE_INDICATOR
from ...forms.departmental_plan import OutPutPerformanceDimensionUpdateForm
from ..helper import PayloadDeserializationStrategyContext, OutputPerformanceDimensionDeserializationStrategy

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
    
    

class OutPutPerformanceDimensionDetailUpdateView(SuccessMessageMixin, UpdateView):
    model = OutPutPerformanceDimension
    form_class = OutPutPerformanceDimensionUpdateForm
    success_message = "Performance dimension was updated successfully!"
    template_name = 'appraisal/departmental_workplan/outputs/performance_dimension/update.html'
    context_object_name = "performance_dimension_form"
    
    def get_object(self, queryset=None):
        repo = OutPutPerformanceDimensionRepository()
        return repo.get_by_id(output_perf_dimension_id=self.kwargs.get("output_performance_dimension_id"))

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["is_quality_indicator"] = False
        if self.get_object().performance_indicator == PERFORMANCE_INDICATOR[1][0]:
            kwargs["is_quality_indicator"] = True
        return kwargs
    
    def get_weight_progress(self):
        return get_perf_dimension_weight_progress(department_output_obj=self.get_object().department_output)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[self.context_object_name] = context.get("form")
        dept_output_progress_data = {
            "weight": self.get_object().department_output.weight,
            "covered_weight": self.get_weight_progress().covered_weight,
            "remain_weight": self.get_weight_progress().remaining_weight
        }
        context.update(**dept_output_progress_data)
        context["perf_dimension_obj"] = self.get_object()
        return context
    
    def payload_validation(self, form):
        payload_strategy = PayloadDeserializationStrategyContext(strategy=OutputPerformanceDimensionDeserializationStrategy())
        return payload_strategy.deserialize_payload(request_object=self.request, form_object=form)
        
    def form_valid(self, form):
        try:
            payload = self.payload_validation(form=form)
            
            if self.get_weight_progress().remaining_weight < payload.weight:
                messages.error(self.request, "The weight cannot be greater than remain departmental output weight. Please adjust weight to ensure it does not exceed the remain departmental output weight.")
                return self.form_invalid(form)

            repo = OutPutPerformanceDimensionRepository()
            perf_dimension_obj = repo.update(
                                            output_perf_dimension_obj=self.get_object(),
                                            data=payload
                                        )
            form.instance = perf_dimension_obj
        except Exception as e:
            logger.error(f"[OutPutPerformanceDimensionDetailUpdateView] with performance dimension id: {self.kwargs.get('output_performance_dimension_id')}, failed with error: {e}")
            messages.error(self.request, f"An unexpected error occurred, please try again")
            return self.form_invalid(form)

        return super().form_valid(form)
    
    def get(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
            if self.object is None:
                logger.warning(f"[OutPutPerformanceDimensionDetailUpdateView] performance dimension with pk: {self.kwargs.get('output_performance_dimension_id')}, not found error")
                return redirect("object_not_found_error", object_name=slugify("Output Performance Dimensions"))
            
        except Exception as e:
            logger.error(f"[OutPutPerformanceDimensionDetailUpdateView] performance dimension with  pk: {self.kwargs.get('output_performance_dimension_id')}, failed with error: {e}")
            return redirect("server_error_view")
        return super().get(request, *args, **kwargs) 
    
    def get_success_url(self):
        return reverse('output_perf_dimension_detail_update', kwargs={"output_performance_dimension_id": self.kwargs.get('output_performance_dimension_id')})

    
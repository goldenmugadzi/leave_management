from typing import Any
from django.views.generic import TemplateView
from ..services.performance import PerformanceReviewService
from ..repository.performance import PerformanceReviewRepository

class PerformanceReviewsTemplateView(TemplateView):
    template_name = "appraisal/performance/index.html"
    
    
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        repository = PerformanceReviewRepository()
        service_handler = PerformanceReviewService(performance_repo=repository)
        context["appraisals"] = service_handler.get_all_performance_use_case()
        return context
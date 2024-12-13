from typing import Any, Dict, List
from django.views.generic import TemplateView
from ..models import KeyResultArea
from ..forms import YearQuarterForm
from ..repository.kra import KRARepository
from ..services.kra import KRAService

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

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context =  super().get_context_data(**kwargs)
        context.update(self.get_year_quarter_form())
        
        query_param_year = self.request.GET.get('year')
        query_param_quarter = self.request.GET.get('quarter')
        
        if query_param_year is not None or query_param_quarter is not None:
            context.update(self.get_all_kra(year=query_param_year, quarter=query_param_quarter))
        return context
    
    
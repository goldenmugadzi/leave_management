from typing import Any, Dict
from django.forms import BaseModelForm
from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic.edit import CreateView
from django.views.generic import TemplateView
from ..forms import YearQuarterForm

class KRATemplateView(TemplateView):
    template_name = 'appraisal/kra/index.html'
    
    def get_year_quarter_form(self)->Dict[str, YearQuarterForm]:
        form = YearQuarterForm(self.request.POST or None)
        data = {"year_quarter_form": form}
        return data

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context =  super().get_context_data(**kwargs)
        context.update(self.get_year_quarter_form())
        print("===========>>>>>>", kwargs)
        return context
    
    def post(self, request, *args, **kwargs):
        form = YearQuarterForm(self.request.POST)
        if form.is_valid():
            year = form.cleaned_data.get('year')
            quarter = form.cleaned_data.get('quarter')
            input()
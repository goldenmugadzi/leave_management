from django.views.generic import ListView, DetailView, CreateView
from .models import PretaskRiskAssessment
from django.urls import reverse_lazy

class PretaskRiskAssessmentListView(ListView):
    model = PretaskRiskAssessment
    template_name = 'pretask_risk_assessment/list.html'
    context_object_name = 'assessments'
    ordering = ['-created_at']

class PretaskRiskAssessmentDetailView(DetailView):
    model = PretaskRiskAssessment
    template_name = 'pretask_risk_assessment/detail.html'
    context_object_name = 'assessment'

class PretaskRiskAssessmentCreateView(CreateView):
    model = PretaskRiskAssessment
    fields = ['task_name', 'risk_level', 'description']
    template_name = 'pretask_risk_assessment/form.html'
    success_url = reverse_lazy('pretask_risk_assessment:list')

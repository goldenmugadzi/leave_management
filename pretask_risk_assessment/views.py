from django.views.generic import ListView, DetailView, CreateView
from .models import PretaskRiskAssessment, Job
from django.urls import reverse_lazy
from .forms import *

class JobListView(ListView):
    model = Job
    template_name = 'pretask_risk_assessment/list.html'
    context_object_name = 'jobs'
    ordering = ['-created_at'] 
    

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
    fields = ['job', 'equipment', 'harzard', 'control_measures']
    template_name = 'pretask_risk_assessment/form.html'
    success_url = reverse_lazy('pretask_risk_assessment:list')

# CreateView for Job

class JobCreateView(CreateView):
    model = Job
    form_class = JobForm
    template_name = 'pretask_risk_assessment/job_form.html'
    success_url = reverse_lazy('pretask_risk_assessment:jobs')



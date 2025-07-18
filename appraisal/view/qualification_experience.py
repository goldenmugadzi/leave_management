from django.views.generic.edit import CreateView, UpdateView
from django.views.generic import TemplateView
from django.urls import reverse, reverse_lazy
from django.utils.text import slugify

from django.shortcuts import redirect
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages

class QualificationExperienceTemplateView(TemplateView):
    template_name = 'appraisal/qualification_experience/index.html'
    
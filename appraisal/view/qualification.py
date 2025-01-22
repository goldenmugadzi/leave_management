from django.forms import BaseModelForm
from django.http import HttpResponse
from django.http import JsonResponse
from django.views.generic.edit import CreateView
from django.views.generic import TemplateView
from ..forms import UserQualificationForm
from it.users.models import UserQualification

class UserQualificationTemplateView(TemplateView):
    template_name = 'appraisal/qualification/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qualification_objects = UserQualification.objects.filter(user__id=self.kwargs.get("user_id"))
        context["qualification_objects"] = qualification_objects
        return context

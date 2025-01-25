from django.forms import BaseModelForm
from django.http import HttpResponse
from django.http import JsonResponse
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.urls import reverse
from django.views.generic.edit import CreateView
from django.views.generic import TemplateView
from ..forms import UserQualificationForm
from it.users.models import UserQualification
from ..repository import UserQualificationRepository
from ..services import UserQualificationService
from approve.forms import ApprovalForm
from loguru import logger

class UserQualificationTemplateView(TemplateView):
    template_name = 'appraisal/qualification/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qualification_objects = UserQualification.objects.filter(user__id=self.kwargs.get("user_id"))
        context["qualification_objects"] = qualification_objects
        return context

class UserQualificationCreateView(SuccessMessageMixin,CreateView):
    model = UserQualification
    form_class = UserQualificationForm
    template_name = 'appraisal/qualification/create_update.html'
    success_message = 'Qualification added successfully'
    context_object_name = "qualification_form"
    
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[self.context_object_name] = context.get("form")
        return context
    
    def form_valid(self, form):
        try:
            form.instance.user = self.request.user
            form.instance.file = self.request.FILES.get("file")
            repo = UserQualificationRepository()
            service_handler = UserQualificationService(user_qualification_repo=repo)
            user_qualification_obj = service_handler.create_use_case(
                user_object=self.request.user,
                name=form.cleaned_data.get("name"),
                file=self.request.FILES.get("file")
            )
            form.instance = user_qualification_obj
        except Exception as e:
            messages.error(self.request, "An unexpected error occurred, please try again")
            logger.error(f"Creating User Qualification View failed with error: {e}")
            return self.form_invalid(form)
        return super().form_valid(form)
    
    def get_success_url(self) -> str:
        return reverse('update_appraisal', kwargs={"pk": self.kwargs.get("appraisal_id")})

class UserQualificationUpdateView(SuccessMessageMixin,CreateView):
    model = UserQualification
    form_class = UserQualificationForm
    template_name = 'appraisal/qualification/create_update.html'
    success_message = 'Qualification updated successfully'
    context_object_name = "qualification_form"
    
    def get_object(self, queryset=None):
        repo = UserQualificationRepository()
        service_handler = UserQualificationService(user_qualification_repo=repo)
        
        obj = service_handler.get_by_pk_use_case(
            qualification_id=self.kwargs.get("qualification_id")
        )
        return obj
    
    
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[self.context_object_name] = context.get("form")
        
        return context
    
    def form_valid(self, form):
        try:
            form.instance.user = self.request.user
            form.instance.file = self.request.FILES.get("file")
            repo = UserQualificationRepository()
            service_handler = UserQualificationService(user_qualification_repo=repo)
            
            user_qualification_obj = service_handler.update_use_case(
                qualification_object_id=self.kwargs.get("qualification_id"),
                name=form.cleaned_data.get("name"),
                file=self.request.FILES.get("file")
            )
            form.instance = user_qualification_obj
        except Exception as e:
            messages.error(self.request, "An unexpected error occurred, please try again")
            logger.error(f"Update User Qualification View failed with error: {e}")
            return self.form_invalid(form)
        return super().form_valid(form)
    
    def get_success_url(self) -> str:
        return reverse('update_qualification', kwargs={"qualification_id": self.kwargs.get("qualification_id")})

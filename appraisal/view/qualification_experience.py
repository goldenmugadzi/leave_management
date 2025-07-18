from django.views.generic.edit import CreateView, UpdateView
from django.views.generic import TemplateView
from django.urls import reverse, reverse_lazy
from django.utils.text import slugify

from django.shortcuts import redirect
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from it.users.models import UserExperience, UserQualification, UserProfile
from ..forms.qualification_experiences import UserExperienceForm, UserQualificationForm
from ..repository.qualification_experience import UserExperienceRepository, UserQualificationRepository
from loguru import logger

def get_user_object_by_id(user_id):
    try:
        qr = UserProfile.objects.filter(id=user_id)
        if not qr.exists():
            return None
        return qr.first()
    except Exception as e:
        raise Exception(f"Handler get_user_object_by_id with this pk: {user_id}, failed with this error: {e}")
        
class QualificationExperienceTemplateView(SuccessMessageMixin, CreateView):
    model = UserQualification
    form_class = UserQualificationForm
    context_object_name = "user_qualification_form"
    template_name = 'appraisal/qualification_experience/index.html'

    def get_experience_form(self):
        return UserExperienceForm(self.request.GET or None)
    
    def get_user_object(self):
        return get_user_object_by_id(user_id=self.kwargs.get('user_id'))
    
    def is_my_qualification_experience(self):
        return self.request.user.id == int(self.kwargs.get('user_id'))
    
    def is_user_qualification_request(self):
        if "user_qualification_request" in self.request.POST:
            return True
        return False
    
    def get_user_experiences(self):
        repo = UserExperienceRepository()
        return repo.fetch_by_user_id(user_id=self.kwargs.get('user_id'))
        
    def get_user_qualification(self):
        repo = UserQualificationRepository()
        return repo.fetch_by_user(user_id=self.kwargs.get('user_id'))
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[self.context_object_name] = context.get("form")
        context["user_experience_form"] = self.get_experience_form()
        
        context["user_experiences_qr"] = self.get_user_experiences()
        context["user_qualification_qr"] = self.get_user_qualification()
        context["user_name"] = self.get_user_object().get_full_name()
        context["is_my_qualification_experience"] = self.is_my_qualification_experience()
        return context
    
    def get(self, request, *args, **kwargs):
        self.object = None
        try:
            if self.get_user_object() is None:
                logger.warning(f"[QualificationExperienceTemplateView] self.get_user_object() with user pk: {self.kwargs.get('user_id')}, not found error")
                return redirect("object_not_found_error", object_name=slugify("User"))
        except Exception as e:
            logger.error(f"[QualificationExperienceTemplateView] get_department_objective_obj() with user pk: {self.kwargs.get('user_id')}, failed with error: {e}")
            return redirect("server_error_view")
        return super().get(request, *args, **kwargs)

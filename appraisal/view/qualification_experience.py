from django.views.generic.edit import CreateView, UpdateView
from django.views.generic import TemplateView
from django.urls import reverse, reverse_lazy
from django.utils.text import slugify

from django.shortcuts import redirect
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import ValidationError
from django.contrib import messages
from it.users.models import UserExperience, UserQualification, UserProfile
from ..forms.qualification_experiences import UserExperienceForm, UserQualificationForm
from ..repository.qualification_experience import UserExperienceRepository, UserQualificationRepository
from datetime import datetime

from loguru import logger

def get_user_object_by_id(user_id):
    try:
        qr = UserProfile.objects.filter(id=user_id)
        if not qr.exists():
            return None
        return qr.first()
    except Exception as e:
        raise Exception(f"Handler get_user_object_by_id with this pk: {user_id}, failed with this error: {e}")
        
class QualificationExperienceTemplateView(TemplateView):
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
        
        context["user_experiences_qr"] = self.get_user_experiences()
        context["user_qualification_qr"] = self.get_user_qualification()
        context["user_object"] = self.get_user_object()
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

class QualificationCreateView(SuccessMessageMixin, CreateView):
    model = UserQualification
    form_class = UserQualificationForm
    context_object_name = "user_qualification_form"
    template_name = 'appraisal/qualification_experience/qualifications/create_update.html'
    success_message = "New qualification added successfully"
    
    def get_user_object(self):
        return get_user_object_by_id(user_id=self.kwargs.get('user_id'))
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[self.context_object_name] = context.get("form")
        
        context["user_object"] = self.get_user_object()
        return context
    

    def form_valid(self, form):
        try:
            form.instance.file = self.request.FILES.get("file")
            repo = UserQualificationRepository()
            user_qualification_obj = repo.create(
                user_object=self.get_user_object(),
                name=form.cleaned_data.get("name"),
                description=form.cleaned_data.get("description"),
                file=self.request.FILES.get("file")
            )
            form.instance = user_qualification_obj
        except Exception as e:
            logger.error(f"[QualificationCreateView] with user id: {self.kwargs.get('user_id')}, failed with error: {e}")
            messages.error(self.request, f"An unexpected error occurred, please try again")
            return self.form_invalid(form)

        return super().form_valid(form)
    
    def get(self, request, *args, **kwargs):
        self.object = None
        try:
            if self.get_user_object() is None:
                logger.warning(f"[QualificationCreateView] get_user_object() with user pk: {self.kwargs.get('user_id')}, not found error")
                return redirect("object_not_found_error", object_name=slugify("User"))
        except Exception as e:
            logger.error(f"[QualificationCreateView] get_user_object() with user pk: {self.kwargs.get('user_id')}, failed with error: {e}")
            return redirect("server_error_view")
        return super().get(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse('qualification_experience_index', kwargs={"user_id": self.kwargs.get('user_id')})
    
class QualificationUpdateView(SuccessMessageMixin, UpdateView):
    model = UserQualification
    form_class = UserQualificationForm
    context_object_name = "user_qualification_form"
    template_name = 'appraisal/qualification_experience/qualifications/create_update.html'
    success_message = "Qualification updated successfully"
    
    def get_object(self, queryset = None):
        repo = UserQualificationRepository()
        return repo.get_by_id(qualification_id=self.kwargs.get('qualification_id'))
    
    def get_user_object(self):
        return self.get_object().user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[self.context_object_name] = context.get("form")
        
        context["user_object"] = self.get_user_object()
        return context
    
    
    def form_valid(self, form):
        try:
            form.instance.file = self.request.FILES.get("file")
            repo = UserQualificationRepository()
            user_qualification_obj = repo.update(
                qualification_object_id=self.kwargs.get('qualification_id'),
                name=form.cleaned_data.get("name"),
                description=form.cleaned_data.get("description"),
                file=self.request.FILES.get("file")
            )
            form.instance = user_qualification_obj
        except Exception as e:
            logger.error(f"[QualificationUpdateView] with qualification id: {self.kwargs.get('qualification_id')}, failed with error: {e}")
            messages.error(self.request, f"An unexpected error occurred, please try again")
            return self.form_invalid(form)

        return super().form_valid(form)
    
    def get(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
            if self.object is None:
                logger.warning(f"[QualificationUpdateView] qualification object with pk: {self.kwargs.get('qualification_id')}, not found error")
                return redirect("object_not_found_error", object_name=slugify("Qualification"))
        except Exception as e:
            logger.error(f"[QualificationCreateView] qualification object with pk: {self.kwargs.get('qualification_id')}, failed with error: {e}")
            return redirect("server_error_view")
        return super().get(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse('qualification_update', kwargs={"qualification_id": self.kwargs.get('qualification_id')})
    

def validate_dates(start_date, end_date):
    today = datetime.now().date()

    if start_date > today:
        raise ValidationError("'Experience from' date cannot be in the future.")

    if end_date is not None:
        if end_date == start_date:
            raise ValidationError("'Experience to' date cannot be the same as 'experience from' date.")
        if end_date < start_date:
            raise ValidationError("'Experience to' date cannot be before 'experience from' date.")
        if end_date > today:
            raise ValidationError("'Experience to' date cannot be in the future.")

class UserExperienceCreateView(SuccessMessageMixin, CreateView):
    model = UserExperience
    form_class = UserExperienceForm
    context_object_name = "user_experience_form"
    template_name = 'appraisal/qualification_experience/experiences/create_update.html'
    success_message = "New experience added successfully"
    
    def get_user_object(self):
        return get_user_object_by_id(user_id=self.kwargs.get('user_id'))
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[self.context_object_name] = context.get("form")
        
        context["user_object"] = self.get_user_object()
        return context
    
    def form_valid(self, form):
        try:
            repo = UserExperienceRepository()
            experience_from_date = form.cleaned_data.get('experience_from')
            experience_to_date = form.cleaned_data.get('experience_to') or None
            
            validate_dates(start_date=experience_from_date, end_date=experience_to_date)
            
            user_experience_obj = repo.create(
                user_object=self.get_user_object(),
                name=form.cleaned_data.get("name"),
                experience_from_date=experience_from_date,
                experience_to_date=experience_to_date
            )
            form.instance = user_experience_obj
        except ValidationError as e:
            messages.error(self.request, e.message)
            return self.form_invalid(form)
        except Exception as e:
            logger.error(f"[UserExperienceCreateView] with user id: {self.kwargs.get('user_id')}, failed with error: {e}")
            messages.error(self.request, f"An unexpected error occurred, please try again")
            return self.form_invalid(form)

        return super().form_valid(form)
    
    def get(self, request, *args, **kwargs):
        self.object = None
        try:
            if self.get_user_object() is None:
                logger.warning(f"[UserExperienceCreateView] get_user_object() with user pk: {self.kwargs.get('user_id')}, not found error")
                return redirect("object_not_found_error", object_name=slugify("User"))
        except Exception as e:
            logger.error(f"[UserExperienceCreateView] get_user_object() with user pk: {self.kwargs.get('user_id')}, failed with error: {e}")
            return redirect("server_error_view")
        return super().get(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse('qualification_experience_index', kwargs={"user_id": self.kwargs.get('user_id')})
    
    
    
class UserExperienceUpdateView(SuccessMessageMixin, UpdateView):
    model = UserExperience
    form_class = UserExperienceForm
    context_object_name = "user_experience_form"
    template_name = 'appraisal/qualification_experience/experiences/create_update.html'
    success_message = "Experience updated successfully"
    
    def get_object(self, queryset = None):
        repo = UserExperienceRepository()
        return repo.get_by_id(user_exp_id=self.kwargs.get('experience_id'))
    
    def get_user_object(self):
        return self.get_object().user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[self.context_object_name] = context.get("form")
        
        context["user_object"] = self.get_user_object()
        return context
    
    def form_valid(self, form):
        try:
            repo = UserExperienceRepository()
            experience_from_date = form.cleaned_data.get('experience_from')
            experience_to_date = form.cleaned_data.get('experience_to') or None
            
            validate_dates(start_date=experience_from_date, end_date=experience_to_date)
            
            user_experience_obj = repo.update(
                user_experience_obj=self.get_object(),
                name=form.cleaned_data.get("name"),
                experience_from_date=experience_from_date,
                experience_to_date=experience_to_date
            )
            form.instance = user_experience_obj
        except ValidationError as e:
            messages.error(self.request, e.message)
            return self.form_invalid(form)
        except Exception as e:
            logger.error(f"[UserExperienceUpdateView] with experience id: {self.kwargs.get('experience_id')}, failed with error: {e}")
            messages.error(self.request, f"An unexpected error occurred, please try again")
            return self.form_invalid(form)

        return super().form_valid(form)
    
    def get(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
            if self.object is None:
                logger.warning(f"[UserExperienceUpdateView] with experience id: {self.kwargs.get('experience_id')}, not found error")
                return redirect("object_not_found_error", object_name=slugify("User"))
        except Exception as e:
            logger.error(f"[UserExperienceUpdateView] with experience id: {self.kwargs.get('experience_id')}, failed with error: {e}")
            return redirect("server_error_view")
        return super().get(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse('user_experience_update', kwargs={"experience_id": self.kwargs.get('experience_id')})
    

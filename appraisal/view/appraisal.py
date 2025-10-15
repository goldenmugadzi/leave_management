from typing import Any, Dict, List, Tuple
from decimal import Decimal
from django.forms import BaseModelForm
from django.http import HttpResponse
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic import TemplateView
from django.urls import reverse
from django.utils.text import slugify

from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponseRedirect
from django.contrib import messages

from ..models import Appraisal, AppraiseePersonalAttribute
from it.users.models import UserProfile, GRADE_CHOICES
from ..forms import AppraisalForm, AppraisalRoleFilterForm, AppraisalUpdateForm
from ..forms.qualification_experiences import UserQualificationsUploadForm
from ..helpers.types.kra import RoleFilterChoices
from ..repository import UserQualificationRepository, AppraisalExperienceRepository, ExperienceRepository, AppraisalRepository
from ..repository.appraisal import AppraiseePersonalAttributeRepository, AppraisalOverallCommentsRepository
from ..repository.kra import AppraisalOutPutPerformanceDimensionScoreRepository, YearQuarterRepository, AppraisalConfirmationStatusRepository
from ..repository.qualification_experience import UserExperienceRepository
from ..repository.users import UserProfileRepository
from ..services import AppraisalService, AppraisalExperienceService
from ..services.qualification import UserQualificationService
from ..services.appraisal import AppraisalPersonalAttributeService
from ..helpers.types.kra import KraRolesType
from ..helpers.getters.approval import ApprovalStagesHandler
from ..helpers.getters.appraisal import AppraisalDependanciesStrategyContext, AppraisalPersonalDetailsStrategy, TrainingAndDevStrategy, PerformanceAssessmentStrategy, PerformanceProgressReviewStrategy, FinalPerformanceAssStrategy
from ..models.kra import REVIEWERS_CONFIRMATION_STATUS, APPRAISAL_KRA_REVIEWER_STATUS_CHOICES
from approve.views import intiate,approve_step
from approve.forms import ApprovalForm
from approve.models import Step, Approval
from datetime import datetime
from ..forms.formsets import AppraiseePersonalAttributeFormSet
from ..forms.kra import AppraisalConfirmationStatusForm
from ..forms.appraisal import AppraisalOverallCommentForm, AppraiseePersonalAttributeForm
from ..helpers.getters.dates import get_assessment_period, CurrentQuarterDate
from ..helpers.getters.quarter import get_all_quarter_ratings_per_appraiser
from loguru import logger

def get_user_by_id(user_id: int)->UserProfile:
    qr = UserProfile.objects.filter(id=user_id)
    if not qr.exists():
        return None
    return qr.first()

class AppraisalCreateView(SuccessMessageMixin, CreateView):
    model = Appraisal
    form_class = AppraisalForm
    success_message = "Appraisal created successfully! Your appraiser will review it shortly and either accept or reject it."
    template_name = 'appraisal/create_update.html'
    context_object_name = "appraisal_form"
    
    def get_user_object(self):
        return self.request.user
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["appraisee_id"] = self.get_user_object().id
        return kwargs

    def get_current_date_assessment(self):
        current_date = datetime.now()
        return get_assessment_period(date_object=current_date)
    
    def get_user_experiences(self, user_id: int):
        repo = UserExperienceRepository()
        return repo.fetch_by_user_id(user_id=user_id)
        
    def get_user_qualification(self, user_id: int):
        repo = UserQualificationRepository()
        return repo.fetch_by_user(user_id=user_id)
    
    def appraisee_grade(self):
        user_obj = self.get_user_object()
        
        if user_obj.grade == GRADE_CHOICES[1][1]:
            return GRADE_CHOICES[1][1]
        
        if user_obj.grade == GRADE_CHOICES[2][1]:
            return "C, D, E and F"
        return ""
    
    def has_no_required_profile_information(self):
        appraisee_object = self.get_user_object()
        
        if not appraisee_object.designation or not appraisee_object.cost_center or not appraisee_object.grade:
            return True
        return False  
    
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context =  super().get_context_data(**kwargs)
        user_object = self.get_user_object()
        context[self.context_object_name] = context.get("form")
        
        context["user_object"] = user_object
        context["has_no_designation"] = self.get_user_object().designation == None or self.get_user_object().designation == ""
        context["assessment_period"] = self.get_current_date_assessment()
        
        context["user_experiences_qr"] = self.get_user_experiences(user_id=user_object.id)
        context["user_qualification_qr"] = self.get_user_qualification(user_id=user_object.id)
        
        can_make_changes = False
        
        if not self.has_no_required_profile_information():
            can_make_changes = True
        context["can_mutate"] = can_make_changes
        context["is_update"] = False
        context["appraisee_grade"] = self.appraisee_grade()
        return context

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        appraisee_object = self.get_user_object()
        
        if not appraisee_object.grade:
            messages.error(self.request, "Oops! Your profile has no grade set. Kindly contact admin.")
            return self.form_invalid(form)

        if not appraisee_object.designation:
            messages.error(self.request, "Oops! Your profile has no designation set. Kindly contact admin.")
            return self.form_invalid(form)
        
        if not appraisee_object.cost_center:
            messages.error(self.request, "Oops! Your profile has no cost center set. Kindly contact admin.")
            return self.form_invalid(form)
        
        appraiser_object = form.cleaned_data.get("appraiser")
        repo = AppraisalRepository()
        appraisal_object = repo.create(appraisee_object=appraisee_object, appraiser_object=appraiser_object)
        form.instance = appraisal_object
        
        return super().form_valid(form)

    def get(self, request, *args, **kwargs):
        self.object = None
        try:
            user_object = self.get_user_object()
            if user_object is None:
                logger.warning(f"[AppraisalCreateView] get_user_object() with user: {user_object}, not found error")
                return redirect("object_not_found_error", object_name=slugify("User"))

            if self.has_no_required_profile_information():
                messages.error(
                        request,
                        "<strong>Incomplete Appraisee Profile</strong>: The profile is missing required details such as designation, cost center, or grade. Please contact the IT department to complete the profile setup."
                    )
                
            messages.info(
                request,
                "<strong>Take Note:</strong> Please ensure your profile is complete — including designation, department, qualifications, and experience — before creating an appraisal. You may add missing details and must set your appraiser as the final step."
            )
        except Exception as e:
            logger.error(f"[AppraisalCreateView] get_user_object() with user: {user_object}, failed with error: {e}")
            return redirect("server_error_view")
        return super().get(request, *args, **kwargs)

    def get_success_url(self) -> str:
        return reverse('appraisal_index')


class AppraisalUpdateView(SuccessMessageMixin, UpdateView):
    model = Appraisal
    form_class = AppraisalUpdateForm
    success_message = "Appraisal reviewer was set successfully"
    template_name = "appraisal/create_update.html"
    
    def get_object(self):
        repo = AppraisalRepository()
        return repo.get_appraisal_by_pk(appraisal_id=self.kwargs.get('appraisal_id'))
    
    def is_appraisee_requesting(self):
        appraisee_object = self.get_object().user
        is_appraisee = appraisee_object == self.request.user
        if is_appraisee:
            return appraisee_object.id
        return None
    
    def is_appraiser_requesting(self):
        appraiser_object = self.get_object().appraiser
        is_appraiser = appraiser_object == self.request.user
        if is_appraiser:
            return appraiser_object.id
        return None
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        appraisee_id = self.is_appraisee_requesting()
        appraiser_id = self.is_appraiser_requesting()
        reviewer = self.get_object().reviewer
        
        if appraisee_id:
            kwargs["appraisee_id"] = appraisee_id
            
            reviewer_id = None
            if reviewer is not None:
                reviewer_id = reviewer.id
            kwargs["appraisal_reviewer_id"] = reviewer_id
        if appraiser_id:
            kwargs["appraiser_id"] = appraiser_id
            kwargs["appraisal_appraisee_id"] = self.get_object().user.id
        return kwargs
    
    def get_current_date_assessment(self):
        appraisal_created_date = self.get_object().created_date
        return get_assessment_period(date_object=appraisal_created_date)
    
    def get_user_experiences(self, user_id: int):
        repo = UserExperienceRepository()
        return repo.fetch_by_user_id(user_id=user_id)
        
    def get_user_qualification(self, user_id: int):
        repo = UserQualificationRepository()
        return repo.fetch_by_user(user_id=user_id)
    
    def appraisee_grade(self):
        user_obj = self.get_object().user
        
        if user_obj.grade == GRADE_CHOICES[1][1]:
            return GRADE_CHOICES[1][1]
        
        if user_obj.grade == GRADE_CHOICES[2][1]:
            return "C, D, E and F"
        return ""
    
    def has_no_required_profile_information(self):
        appraisee_object = self.get_object().user
        
        if not appraisee_object.designation or not appraisee_object.cost_center or not appraisee_object.grade:
            return True
        return False   
    
    def get_approval_stages(self):
        try:
            appraisal_object = self.get_object()
            handler = ApprovalStagesHandler(appraisal_id=appraisal_object.id)
            return handler.get_stages_info()
        except Exception as e:
            logger.error(f"[AppraisalUpdateView] get_approval_stages for Appraisal pk: {appraisal_object.id} failed with error: {e}")
            return None    

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context =  super().get_context_data(**kwargs)
        appraisal_object = self.get_object()
        appraisee_object = appraisal_object.user
        
        context[self.context_object_name] = context.get("form")
        context.update(self.get_approval_stages())
        
        context["appraiser_object"] = appraisal_object.appraiser
        context["reviewer_object"] = appraisal_object.reviewer
        context["user_object"] = appraisee_object
        context["has_no_designation"] = appraisee_object.designation == None or appraisee_object.designation == ""
        context["assessment_period"] = self.get_current_date_assessment()
        
        context["user_experiences_qr"] = self.get_user_experiences(user_id=appraisee_object.id)
        context["user_qualification_qr"] = self.get_user_qualification(user_id=appraisee_object.id)
        context["appraisee_grade"] = self.appraisee_grade()

        can_make_changes = False
        
        if self.is_appraisee_requesting() or self.is_appraiser_requesting():
            if not self.has_no_required_profile_information():
                can_make_changes = True
        
        context["can_mutate"] = can_make_changes
        context["is_update"] = True
        return context
    
    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        appraisal_object = self.get_object()
        appraisee_object = appraisal_object.user
        
        if not appraisee_object.grade:
            messages.error(self.request, "Oops! Your profile has no grade set. Kindly contact admin.")
            return self.form_invalid(form)

        if not appraisee_object.designation:
            messages.error(self.request, "Oops! Your profile has no designation set. Kindly contact admin.")
            return self.form_invalid(form)
        
        if not appraisee_object.cost_center:
            messages.error(self.request, "Oops! Your profile has no cost center set. Kindly contact admin.")
            return self.form_invalid(form)
        
        appraiser_object = form.cleaned_data.get("appraiser")
        reviewer_object = form.cleaned_data.get("reviewer")
        hr_obj = form.cleaned_data.get("hr")
        
        repo = AppraisalRepository()
        appraisal_object = repo.update(
            appraisal_object=appraisal_object,
            appraiser_object=appraiser_object,
            reviewer_obj=reviewer_object,
            hr_object=hr_obj
        )
        form.instance = appraisal_object
        
        return super().form_valid(form)

    def get(self, request, *args, **kwargs):
        try:
            appraisal_object = self.get_object()
            self.object = appraisal_object
            if appraisal_object is None:
                logger.warning(f"[AppraisalUpdateView] get_object() with appraisal pk: {appraisal_object.id}, not found error")
                return redirect("object_not_found_error", object_name=slugify("Appraisal"))

            if self.has_no_required_profile_information():
                messages.error(
                        request,
                        "<strong>Incomplete Appraisee Profile</strong>: The profile is missing required details such as designation, cost center, or grade. Please contact the IT department to complete the profile setup."
                    )
            messages.info(
                request,
                "<strong>Take Note:</strong> Please ensure appraisee's profile is complete — including designation, department, qualifications, and experience — before making updates."
            )
        except Exception as e:
            logger.error(f"[AppraisalUpdateView]  get_object() with appraisal pk: {appraisal_object.id}, failed with error: {e}")
            return redirect("server_error_view")
        return super().get(request, *args, **kwargs)

    def get_success_url(self) -> str:
        return reverse('update_appraisal', kwargs={"appraisal_id": self.kwargs.get('appraisal_id')})


class AppraisalTemplateView(TemplateView):
    template_name = 'appraisal/index.html'
    
    def get_role_filter(self)->str:
        role_filter = self.request.GET.get('role_filter')
        if role_filter is None:
            return RoleFilterChoices.MY_APPRAISAL.value
        return role_filter
    
    def get_heading_name(self)->str:
        role_filter = self.get_role_filter()
        return role_filter.capitalize().replace("_", " ")
    
    def get_role_filter_form(self)->Dict[str, AppraisalRoleFilterForm]:
        form = AppraisalRoleFilterForm(initial={"role_filter": self.get_role_filter()})
        return {"role_filter_form": form}
    
    def get_user_qualification_upload_form(self):
        return UserQualificationsUploadForm(self.request.GET)

    def handle_user_qualification_upload_form(self):
        form = UserQualificationsUploadForm(self.request.POST, self.request.FILES)
        if form.is_valid():
            qualifications_file = form.cleaned_data['qualifications_file']
            
            try:
                service = UserQualificationService(
                    user_qualification_repo=UserQualificationRepository()
                )
                service.create_in_bulk_use_case(
                    file=qualifications_file
                ) 
            except Exception as e:
                logger.error(f"[AppraisalTemplateView] qualification failed with error: {e}")
                # ✅ Here you can process the Excel file
            
            messages.success(self.request, "Qualifications file uploaded successfully.")
            return True
        else:
            messages.error(self.request, "Invalid file upload. Please upload a valid Excel file.")
            return False

    def post(self, request, *args, **kwargs):
        """Handle file upload via POST request."""
        if 'qualifications_file' in request.FILES:
            success = self.handle_user_qualification_upload_form()
            if success:
                return HttpResponseRedirect(reverse('appraisal_index'))
        return self.get(request, *args, **kwargs)
    
    def get_appraisals(self)->List[Appraisal]:
        appraisal_service_handler = AppraisalService(
            appraisal_experience_repository=AppraisalExperienceRepository(),
            qualification_repository=UserQualificationRepository(),
            experience_repository=ExperienceRepository(),
            appraisal_repository=AppraisalRepository()
        )
        
        match self.get_role_filter():
            case RoleFilterChoices.MY_APPRAISAL.value:
                return {"appraisals": appraisal_service_handler.get_appraisal_by_user_use_case(user_id=self.request.user.id)}
            case RoleFilterChoices.ASSIGNED_APPRAISALS.value:
                return {"appraisals": appraisal_service_handler.get_appraisal_by_appraiser_use_case(appraiser_id=self.request.user.id)}
            case RoleFilterChoices.APPRAISALS_FOR_REVIEW.value:
                return {"appraisals": appraisal_service_handler.get_appraisal_by_reviewer_use_case(reviewer_id=self.request.user.id)}
            case RoleFilterChoices.ALL_APPRAISALS.value:
                return {"appraisals": appraisal_service_handler.get_all_use_case(hr_id=self.request.user.id)}
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context =  super().get_context_data(**kwargs)
        
        context.update(self.get_role_filter_form())
        context.update({"heading_name": self.get_heading_name()})
        context.update(self.get_appraisals())
        context.update({"qualification_upload_form": self.get_user_qualification_upload_form()})

        return context
    
    


def internal_server_error_view(request):
    return render(request, "appraisal/server_errors.html", status=500)

def object_not_found_error_view(request, object_name: str):
    object_name = object_name.replace("-", " ")
    context = {
        "object_name": object_name
    }
    return render(request, "appraisal/not_found_error.html", context=context, status=404)


class AppraiseePersonalAttributesDetailView(TemplateView):
    template_name = "appraisal/final_result/index.html"
    
    def get_appraisal_object(self):
        obj = get_object_or_404(Appraisal, pk=self.kwargs.get("appraisal_id"))
        return obj

    def get_all_quarters_apraisee_personal_attrs(self):
        try:
            service_handler = AppraisalPersonalAttributeService(repo=AppraiseePersonalAttributeRepository())
            return service_handler.get_all_quarters(appraisal_obj=self.get_appraisal_object())
        except Exception as e:
            logger.error(f"[AppraiseePersonalAttributesDetailView] get_all_quarters_apraisee_personal_attrs failed with error: {e}")
    
    
    def requesters(self)->Dict[str, bool]:
        appraisal_object = self.get_appraisal_object()
        is_appraiser = self.request.user == appraisal_object.appraiser
        is_appraisee = self.request.user == appraisal_object.user
        is_reviewer = self.request.user == appraisal_object.reviewer
        
        data = {
            "is_appraiser": is_appraiser,
            "is_appraisee": is_appraisee,
            "is_reviewer": is_reviewer
        }
        return data
    
    def get_final_comment_form(self, request):
        repo = AppraisalOverallCommentsRepository()
        overall_comm_qr = repo.fetch_by_appraisal_id(appraisal_id=self.kwargs.get("appraisal_id"))
        requesters_dict = self.requesters()

        quarter_forms = {
            "first_quarter": AppraisalOverallCommentForm(
                    request,
                    is_appraiser=requesters_dict["is_appraiser"],
                    instance=overall_comm_qr.filter(quarter__quarter=1).first()
                ),
            "second_quarter": AppraisalOverallCommentForm(
                    request,
                    is_appraiser=requesters_dict["is_appraiser"],
                    instance=overall_comm_qr.filter(quarter__quarter=2).first()
                ),
            "third_quarter": AppraisalOverallCommentForm(
                    request,
                    is_appraiser=requesters_dict["is_appraiser"],
                    instance=overall_comm_qr.filter(quarter__quarter=3).first()
                ),
            "fourth_quarter": AppraisalOverallCommentForm(
                    request,
                    is_appraiser=requesters_dict["is_appraiser"],
                    instance=overall_comm_qr.filter(quarter__quarter=4).first()
                ),
        }
        return quarter_forms
    
    def get_quarterly_total_score(self):
        appraisal_object = self.get_appraisal_object()
        appraisal_created_year = appraisal_object.created_date.year
        return get_all_quarter_ratings_per_appraiser(year=appraisal_created_year, appraisal_id=appraisal_object.id)

    def appraisee_grade(self):
        user_obj = self.get_appraisal_object().user
        
        if user_obj.grade == GRADE_CHOICES[1][1]:
            return GRADE_CHOICES[1][1]
        
        if user_obj.grade == GRADE_CHOICES[2][1]:
            return "C, D, E and F"
        return ""

    def is_current_date_in_current_quarter(self)->bool:
        appraisal_object = self.get_appraisal_object()
        handler = CurrentQuarterDate(year=appraisal_object.created_date.year)
        current_quarter = handler.get_current_quarter()
        
        if current_quarter.is_within_first_quarter:
            return True
        elif current_quarter.is_within_second_quarter:
            return True
        elif current_quarter.is_within_third_quarter:
            return True
        elif current_quarter.is_within_fourth_quarter:
            return True
        return False
    
    def get_appraisal_confirmation_form(self, request):
        repo = AppraisalConfirmationStatusRepository()
        confirmation_status_qr = repo.fetch_by_appraisal_id(appraisal_id=self.kwargs.get("appraisal_id"))
        
        quarter_forms = {
            "first_quarter": 
                {
                    "reviewer_form": AppraisalConfirmationStatusForm(
                    request,
                    instance=confirmation_status_qr.filter(year_quarter__quarter=1, confirmed_by=REVIEWERS_CONFIRMATION_STATUS[1][0]).first()
                ),
                    "hr_form":
                        AppraisalConfirmationStatusForm(
                        request,
                        instance=confirmation_status_qr.filter(year_quarter__quarter=1, confirmed_by=REVIEWERS_CONFIRMATION_STATUS[2][0]).first()
                )
                },
            "second_quarter": {
                    "reviewer_form": AppraisalConfirmationStatusForm(
                    request,
                    instance=confirmation_status_qr.filter(year_quarter__quarter=2, confirmed_by=REVIEWERS_CONFIRMATION_STATUS[1][0]).first()
                ),
                    "hr_form":
                        AppraisalConfirmationStatusForm(
                        request,
                        instance=confirmation_status_qr.filter(year_quarter__quarter=2, confirmed_by=REVIEWERS_CONFIRMATION_STATUS[2][0]).first()
                )
                },
            "third_quarter": {
                    "reviewer_form": AppraisalConfirmationStatusForm(
                    request,
                    instance=confirmation_status_qr.filter(year_quarter__quarter=3, confirmed_by=REVIEWERS_CONFIRMATION_STATUS[1][0]).first()
                ),
                    "hr_form":
                        AppraisalConfirmationStatusForm(
                        request,
                        instance=confirmation_status_qr.filter(year_quarter__quarter=3, confirmed_by=REVIEWERS_CONFIRMATION_STATUS[2][0]).first()
                )
                },
            "fourth_quarter": {
                    "reviewer_form": AppraisalConfirmationStatusForm(
                    request,
                    instance=confirmation_status_qr.filter(year_quarter__quarter=4, confirmed_by=REVIEWERS_CONFIRMATION_STATUS[1][0]).first()
                ),
                    "hr_form":
                        AppraisalConfirmationStatusForm(
                        request,
                        instance=confirmation_status_qr.filter(year_quarter__quarter=4, confirmed_by=REVIEWERS_CONFIRMATION_STATUS[2][0]).first()
                )
                }
        }
        return quarter_forms
    
    def get_current_quarter_type(self):
        appraisal_object = self.get_appraisal_object()
        handler = CurrentQuarterDate(year=appraisal_object.created_date.year)
        return handler.get_current_quarter()
    
    def is_all_scored(self):
        repo = AppraisalOutPutPerformanceDimensionScoreRepository()
        current_quarter = self.get_current_quarter_type()
        data = {
            "first_quarter": False,
            "second_quarter": False,
            "third_quarter": False,
            "fourth_quarter": False,
        }
        if current_quarter.is_within_first_quarter:
            scores_qr = repo.fetch_by_appraisal_id_quarter_num(appraisal_id=self.kwargs.get("appraisal_id"), quarter_num=1)
            not_scored_qr = scores_qr.filter(is_scored=False)
            if not not_scored_qr.exists():
                data["first_quarter"] = True
        if current_quarter.is_within_second_quarter:
            scores_qr = repo.fetch_by_appraisal_id_quarter_num(appraisal_id=self.kwargs.get("appraisal_id"), quarter_num=2)
            not_scored_qr = scores_qr.filter(is_scored=False)
            if not not_scored_qr.exists():
                data["second_quarter"] = True
        if current_quarter.is_within_third_quarter:
            scores_qr = repo.fetch_by_appraisal_id_quarter_num(appraisal_id=self.kwargs.get("appraisal_id"), quarter_num=3)
            not_scored_qr = scores_qr.filter(is_scored=False)
            if not not_scored_qr.exists():
                data["third_quarter"] = True
        if current_quarter.is_within_fourth_quarter:
            scores_qr = repo.fetch_by_appraisal_id_quarter_num(appraisal_id=self.kwargs.get("appraisal_id"), quarter_num=4)
            not_scored_qr = scores_qr.filter(is_scored=False)
            if not not_scored_qr.exists():
                data["fourth_quarter"] = True
        return data
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        final_rating_type = self.get_quarterly_total_score()

        context.update(self.requesters())
        context["appraisal_object"] = self.get_appraisal_object()
        context["appraisee_personal_attr_qr"] = self.get_all_quarters_apraisee_personal_attrs()
        context["quarter_ratings"] = final_rating_type.rating
        context["final_score"] = final_rating_type.final_score
        context["final_comment_form"] = self.get_final_comment_form(None)
        context["appraisee_grade"] = self.appraisee_grade()
        context["is_detail_view"] = False
        context["appraisal_confirmation_forms"] = self.get_appraisal_confirmation_form(None)
        context["current_quarter"] = self.get_current_quarter_type()
        context["is_all_scored"] = self.is_all_scored()

        return context
    
    def get_quarter_in_post_request(self):
        quarter_number = None
        
        if "First Quarter" in self.request.POST:
            quarter_number = 1
        elif "Second Quarter" in self.request.POST:
            quarter_number = 2
        elif "Third Quarter" in self.request.POST:
            quarter_number = 3
        elif "Fourth Quarter" in self.request.POST:
            quarter_number = 4
        return quarter_number
    
    def post(self, request, *args, **kwargs):
        try:
            appraisal_object = self.get_appraisal_object()
            
            quarter_number = self.get_quarter_in_post_request()
            if quarter_number is None:
                raise Exception(f"AppraisalOverallComments has no quarter num in request")
            
            if quarter_number == 1:
                form = self.get_final_comment_form(request.POST).get("first_quarter")
            elif quarter_number == 2:
                form = self.get_final_comment_form(request.POST).get("second_quarter")
            elif quarter_number == 3:
                form = self.get_final_comment_form(request.POST).get("third_quarter")
            else:
                form = self.get_final_comment_form(request.POST).get("fourth_quarter")

            if form.is_valid():
                repo = AppraisalOverallCommentsRepository()
                obj = repo.get_by_appraisal_id_quarter_id(
                    appraisal_id=self.get_appraisal_object().id,
                    quarter_number=quarter_number
                )
                
                if obj is None:
                    raise Exception(f"AppraisalOverallComments with quarter num {quarter_number} not found")
                
                repo.update(
                    appraisal_overall_comm_obj=obj,
                    comment=form.cleaned_data.get("appraiser_comment", None)
                )
                messages.success(request, f"Overall comments added successfully")
            else:
                error_messages = ""
                for error_message in form.errors:
                    msg = f"{error_message['msg']}: '{error_message['loc'][0]}'"
                    error_messages.join(msg)
                messages.error(request, error_messages)
        except Exception as e:
            logger.error(f"[AppraiseePersonalAttributesDetailView] setting overall comment for appraisal pk: {appraisal_object.id}, failed with error: {e}")
            messages.error(request, "Something went wrong, please contact the admin")

        return redirect(reverse("appraisal_final_result_index", kwargs={"appraisal_id": self.kwargs.get("appraisal_id")}))

    def get(self, request, *args, **kwargs):
        try:
            appraisal_id = self.kwargs.get('appraisal_id')
            appraisal_object = self.get_appraisal_object()
            if appraisal_object is None:
                logger.warning(f"[AppraiseePersonalAttributesDetailView] get_appraisal_object() with appraisal pk: {appraisal_id}, not found error")
                return redirect("object_not_found_error", object_name=slugify("Appraisal"))

            self.get_all_quarters_apraisee_personal_attrs()
        except Exception as e:
            logger.error(f"[AppraiseePersonalAttributesDetailView]  get_appraisal_object() with appraisal pk: {appraisal_id}, failed with error: {e}")
            return redirect("server_error_view")
        return super().get(request, *args, **kwargs)
    
class AppraiseePersonalAttributesUpdateView(TemplateView):
    template_name = 'appraisal/final_result/update.html'
    
    def get_appraisal_object(self):
        obj = get_object_or_404(Appraisal, pk=self.kwargs.get("appraisal_id"))
        return obj
    
    def approval_user_roles(self)->Dict[str, bool]:
        is_appraiser = self.request.user == self.get_appraisal_object().appraiser
        data = {
            "is_appraiser": is_appraiser,
        }
        return data
    
    def get_quarter_personal_attr(self):
        repo = AppraiseePersonalAttributeRepository()
        return repo.fetch_appraisal_id_quarter_id(appraisal_id=self.kwargs.get("appraisal_id"),
                                                quarter_id=self.kwargs.get("quarter_id"))

    def get_forms(self):
        qr =  self.get_quarter_personal_attr()   
        formset_data = []
        
        for appraisee_personal_attr_obj in qr:
            data = {
                    "personal_attribute": appraisee_personal_attr_obj.personal_attribute,
                    "excellent": appraisee_personal_attr_obj.excellent,
                    "very_good": appraisee_personal_attr_obj.very_good,
                    "satisfactory": appraisee_personal_attr_obj.satisfactory,
                    "requires_improvement": appraisee_personal_attr_obj.requires_improvement,
                    "unsatisfactory": appraisee_personal_attr_obj.unsatisfactory
                    }
            formset_data.append(data)
        if self.request.method == "POST":
            formset = AppraiseePersonalAttributeFormSet(
                        self.request.POST or None,
                        initial=formset_data,
                        prefix="appraisee_personal_attribute"
                    )
            
            return formset
        else:
            formset = AppraiseePersonalAttributeFormSet(
                        initial=formset_data,
                        prefix="appraisee_personal_attribute"
                    )
            
            return formset
    
    def appraisee_grade(self):
        user_obj = self.get_appraisal_object().user
        
        if user_obj.grade == GRADE_CHOICES[1][1]:
            return GRADE_CHOICES[1][1]
        
        if user_obj.grade == GRADE_CHOICES[2][1]:
            return "C, D, E and F"
        return ""
    
    
    def get_year_quarter_obj(self):
        repo = YearQuarterRepository()
        return repo.get_by_year_quarter_id(quarter_id=self.kwargs.get("quarter_id"))
    
    def is_current_date_in_current_quarter(self)->bool:
        appraisal_object = self.get_appraisal_object()
        handler = CurrentQuarterDate(year=appraisal_object.created_date.year)
        current_q_type = handler.get_current_quarter()
        current_quarter_obj = self.get_year_quarter_obj()

        match current_quarter_obj.quarter:
            case 1:
                return current_q_type.is_within_first_quarter
            case 2:
                return current_q_type.is_within_second_quarter
            case 3:
                return current_q_type.is_within_third_quarter
            case _:
                
                return current_q_type.is_within_fourth_quarter
    
    def is_all_scored(self):
        repo = AppraisalOutPutPerformanceDimensionScoreRepository()
        scores_qr = repo.fetch_by_appraisal_id_year_quarter_id(appraisal_id=self.kwargs.get("appraisal_id"),
                                                               year_quarter_id=self.kwargs.get("quarter_id")
                                                               )
        not_scored_qr = scores_qr.filter(is_scored=False)
        
        if not_scored_qr.exists():
            return False
        return True
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.approval_user_roles())
        context["personal_attribute_formset"] = self.get_forms()
        context["appraisal_object"] = self.get_appraisal_object()
        context["appraisee_grade"] = self.appraisee_grade()
        context["is_within_current_quarter"] = self.is_current_date_in_current_quarter()
        context["current_quarter_obj"] = self.get_year_quarter_obj()       
        context["is_all_scored"] = self.is_all_scored()
        context["is_detail_view"] = False
        return context
    
    def get_success_url(self) -> str:
        """
        Redirects to the index page after successful update.
        """
        return reverse('appraisal_personal_attribute_update', kwargs={"appraisal_id": self.kwargs.get('appraisal_id'), "quarter_id": self.kwargs.get('quarter_id')})

    def post(self, request, *args, **kwargs):
        
        appraisal_object = self.get_appraisal_object()
        appraisee_personal_attr_qr = self.get_quarter_personal_attr()
        formset = self.get_forms()
        
        if formset.is_valid():
            err_msg_list = []
            updated_objects = []
            for form in formset:
                cleaned_data = form.cleaned_data
                personal_attribute_obj = cleaned_data.get("personal_attribute")

                excellent = cleaned_data.get("excellent")
                very_good = cleaned_data.get("very_good")
                satisfactory = cleaned_data.get("satisfactory")
                requires_improvement = cleaned_data.get("requires_improvement")
                unsatisfactory = cleaned_data.get("unsatisfactory")
                
                fields = [excellent, very_good, satisfactory, requires_improvement, unsatisfactory]
                if True not in fields:
                    err_msg = f"<strong>{personal_attribute_obj}</strong>: should have at least one tick"
                    err_msg_list.append(err_msg)
                else:
                    # =========  update fields in the model instance ========
                    obj = appraisee_personal_attr_qr.filter(personal_attribute__id=personal_attribute_obj.id).first()
                    obj.excellent=excellent
                    obj.very_good=very_good
                    obj.satisfactory=satisfactory
                    obj.requires_improvement=requires_improvement
                    obj.unsatisfactory=unsatisfactory
                    updated_objects.append(obj)
            if len(err_msg_list) != 0:
                # =============== validation errors ============
                full_error_message = "<br>".join(err_msg_list)
                messages.error(request, full_error_message)
                context = self.get_context_data()
                context["personal_attribute_formset"] = formset
                return self.render_to_response(context)    
            
            try:
                repo = AppraiseePersonalAttributeRepository()
                if repo.bulk_update(updated_objects_list=updated_objects):
                    messages.success(request, "Appraisee personal attributes updated successfully.")

            except Exception as e:
                logger.error(f"[AppraiseePersonalAttributesUpdateView] for appraisal pk: {appraisal_object.id}, failed with error: {e}")
                messages.error(request, "Something went wrong, please contact admin")
        else:
            error_messages = ""
            for error_message in formset.errors:
                msg = f"{error_message['msg']}: '{error_message['loc'][0]}'"
                error_messages.join(msg)
            messages.error(request, error_messages)
        
        return redirect(self.get_success_url())

    def get(self, request, *args, **kwargs):
        try:
            appraisal_id = self.kwargs.get('appraisal_id')
            appraisal_object = self.get_appraisal_object()
            self.object = appraisal_object
            if appraisal_object is None:
                logger.warning(f"[AppraiseePersonalAttributesUpdateView] get_appraisal_object() with appraisal pk: {appraisal_id}, not found error")
                return redirect("object_not_found_error", object_name=slugify("Appraisal"))

        except Exception as e:
            logger.error(f"[AppraiseePersonalAttributesUpdateView]  get_appraisal_object() with appraisal pk: {appraisal_id}, failed with error: {e}")
            return redirect("server_error_view")
        return super().get(request, *args, **kwargs)
    

class AppraisalDetailView(TemplateView):
    template_name = 'appraisal/detail.html'
    
    def get_appraisal_obj(self):
        repo = AppraisalRepository()
        return repo.get_appraisal_by_pk(appraisal_id=self.kwargs.get('appraisal_id'))

    def get_steps(self):
        steps = [
                (1, "Personal Details"),
                (2, "Performance Plan and Assessment"),
                (3, "Training and Development Needs"),
                (4, "Performance Progress Review"),
                (5, "Final Performance Assessment and Rating"),
            ]
        return steps
    
    def get_personal_details(self):
        personal_detail_strg = AppraisalPersonalDetailsStrategy(appraisal_object=self.get_appraisal_obj())
        handler = AppraisalDependanciesStrategyContext(
            strategy=personal_detail_strg
        )
        return handler.get_dependance()
    
    def get_current_date_assessment(self):
        appraisal_created_date = self.get_appraisal_obj().created_date
        return get_assessment_period(date_object=appraisal_created_date)
    
    def get_training_dev(self):
        training_dev_strg = TrainingAndDevStrategy(appraisal_object=self.get_appraisal_obj())
        handler = AppraisalDependanciesStrategyContext(
            strategy=training_dev_strg
        )
        return handler.get_dependance()
    
    def get_perf_assmt(self):
        perf_assmt_strg = PerformanceAssessmentStrategy(appraisal_object=self.get_appraisal_obj())
        handler = AppraisalDependanciesStrategyContext(
            strategy=perf_assmt_strg
        )
        return handler.get_dependance()
    
    def get_perf_progress_rev(self):
        perf_progress_rev_strg = PerformanceProgressReviewStrategy(appraisal_object=self.get_appraisal_obj())
        handler = AppraisalDependanciesStrategyContext(
            strategy=perf_progress_rev_strg
        )
        return handler.get_dependance()
    
    def get_final_score(self):
        appraisal_object = self.get_appraisal_obj()
        appraisal_created_year = appraisal_object.created_date.year
        return get_all_quarter_ratings_per_appraiser(year=appraisal_created_year, appraisal_id=appraisal_object.id)

    
    def get_all_quarters_apraisee_personal_attrs(self):
        try:
            service_handler = AppraisalPersonalAttributeService(repo=AppraiseePersonalAttributeRepository())
            return service_handler.get_all_quarters(appraisal_obj=self.get_appraisal_obj())
        except Exception as e:
            logger.error(f"[AppraiseePersonalAttributesDetailView] get_all_quarters_apraisee_personal_attrs failed with error: {e}")
    
    def get_final_comment_form(self, request):
        repo = AppraisalOverallCommentsRepository()
        overall_comm_qr = repo.fetch_by_appraisal_id(appraisal_id=self.kwargs.get("appraisal_id"))
        
        quarter_forms = {
            "first_quarter": AppraisalOverallCommentForm(
                    request,
                    instance=overall_comm_qr.filter(quarter__quarter=1).first()
                ),
            "second_quarter": AppraisalOverallCommentForm(
                    request,
                    instance=overall_comm_qr.filter(quarter__quarter=2).first()
                ),
            "third_quarter": AppraisalOverallCommentForm(
                    request,
                    instance=overall_comm_qr.filter(quarter__quarter=3).first()
                ),
            "fourth_quarter": AppraisalOverallCommentForm(
                    request,
                    instance=overall_comm_qr.filter(quarter__quarter=4).first()
                ),
        }
        return quarter_forms
    
    def get_appraisal_confirmation_form(self, request):
        repo = AppraisalConfirmationStatusRepository()
        confirmation_status_qr = repo.fetch_by_appraisal_id(appraisal_id=self.kwargs.get("appraisal_id"))
        
        quarter_forms = {
            "first_quarter": 
                {
                    "reviewer_form": AppraisalConfirmationStatusForm(
                    request,
                    instance=confirmation_status_qr.filter(year_quarter__quarter=1, confirmed_by=REVIEWERS_CONFIRMATION_STATUS[1][0]).first()
                ),
                    "hr_form":
                        AppraisalConfirmationStatusForm(
                        request,
                        instance=confirmation_status_qr.filter(year_quarter__quarter=1, confirmed_by=REVIEWERS_CONFIRMATION_STATUS[2][0]).first()
                )
                },
            "second_quarter": {
                    "reviewer_form": AppraisalConfirmationStatusForm(
                    request,
                    instance=confirmation_status_qr.filter(year_quarter__quarter=2, confirmed_by=REVIEWERS_CONFIRMATION_STATUS[1][0]).first()
                ),
                    "hr_form":
                        AppraisalConfirmationStatusForm(
                        request,
                        instance=confirmation_status_qr.filter(year_quarter__quarter=2, confirmed_by=REVIEWERS_CONFIRMATION_STATUS[2][0]).first()
                )
                },
            "third_quarter": {
                    "reviewer_form": AppraisalConfirmationStatusForm(
                    request,
                    instance=confirmation_status_qr.filter(year_quarter__quarter=3, confirmed_by=REVIEWERS_CONFIRMATION_STATUS[1][0]).first()
                ),
                    "hr_form":
                        AppraisalConfirmationStatusForm(
                        request,
                        instance=confirmation_status_qr.filter(year_quarter__quarter=3, confirmed_by=REVIEWERS_CONFIRMATION_STATUS[2][0]).first()
                )
                },
            "fourth_quarter": {
                    "reviewer_form": AppraisalConfirmationStatusForm(
                    request,
                    instance=confirmation_status_qr.filter(year_quarter__quarter=4, confirmed_by=REVIEWERS_CONFIRMATION_STATUS[1][0]).first()
                ),
                    "hr_form":
                        AppraisalConfirmationStatusForm(
                        request,
                        instance=confirmation_status_qr.filter(year_quarter__quarter=4, confirmed_by=REVIEWERS_CONFIRMATION_STATUS[2][0]).first()
                )
                }
        }
        return quarter_forms
    
    def requesters(self)->Dict[str, bool]:
        appraisal_object = self.get_appraisal_obj()
        is_appraiser = self.request.user == appraisal_object.appraiser
        is_appraisee = self.request.user == appraisal_object.user
        is_reviewer = self.request.user == appraisal_object.reviewer
        is_hr = self.request.user == appraisal_object.hr
        
        data = {
            "is_appraiser": is_appraiser,
            "is_appraisee": is_appraisee,
            "is_reviewer": is_reviewer,
            "is_hr": is_hr
        }
        return data
    
    def get_current_quarter_type(self):
        appraisal_object = self.get_appraisal_obj()
        handler = CurrentQuarterDate(year=appraisal_object.created_date.year)
        return handler.get_current_quarter()
    
    def is_current_date_in_current_quarter(self)->bool:
        current_quarter = self.get_current_quarter_type()
        
        if current_quarter.is_within_first_quarter:
            return True
        elif current_quarter.is_within_second_quarter:
            return True
        elif current_quarter.is_within_third_quarter:
            return True
        elif current_quarter.is_within_fourth_quarter:
            return True
        return False
    
    def get_quarter_num(self):
        current_quarter = self.get_current_quarter_type()
        
        if current_quarter.is_within_first_quarter:
            return 1
        elif current_quarter.is_within_second_quarter:
            return 2
        elif current_quarter.is_within_third_quarter:
            return 3
        elif current_quarter.is_within_fourth_quarter:
            return 4
    
    def is_all_scored(self):
        repo = AppraisalOutPutPerformanceDimensionScoreRepository()
        current_quarter = self.get_current_quarter_type()
        data = {
            "first_quarter": False,
            "second_quarter": False,
            "third_quarter": False,
            "fourth_quarter": False,
        }
        if current_quarter.is_within_first_quarter:
            scores_qr = repo.fetch_by_appraisal_id_quarter_num(appraisal_id=self.kwargs.get("appraisal_id"), quarter_num=1)
            not_scored_qr = scores_qr.filter(is_scored=False)
            if not not_scored_qr.exists():
                data["first_quarter"] = True
        if current_quarter.is_within_second_quarter:
            scores_qr = repo.fetch_by_appraisal_id_quarter_num(appraisal_id=self.kwargs.get("appraisal_id"), quarter_num=2)
            not_scored_qr = scores_qr.filter(is_scored=False)
            if not not_scored_qr.exists():
                data["second_quarter"] = True
        if current_quarter.is_within_third_quarter:
            scores_qr = repo.fetch_by_appraisal_id_quarter_num(appraisal_id=self.kwargs.get("appraisal_id"), quarter_num=3)
            not_scored_qr = scores_qr.filter(is_scored=False)
            if not not_scored_qr.exists():
                data["third_quarter"] = True
        if current_quarter.is_within_fourth_quarter:
            scores_qr = repo.fetch_by_appraisal_id_quarter_num(appraisal_id=self.kwargs.get("appraisal_id"), quarter_num=4)
            not_scored_qr = scores_qr.filter(is_scored=False)
            if not not_scored_qr.exists():
                data["fourth_quarter"] = True
        return data
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        final_rating_type = self.get_final_score()
        context.update(self.requesters())
        context["appraisal_obj"] = self.get_appraisal_obj()
        context["steps"] = self.get_steps()
        context["personal_details"] = self.get_personal_details()
        context["assessment_period"] = self.get_current_date_assessment()
        context["training_dev_data"] = self.get_training_dev()
        context["perf_assessment_data"] = self.get_perf_assmt()
        context["perf_progress_data"] = self.get_perf_progress_rev()
        context["final_stage_data"] = final_rating_type.rating
        context["final_score"] = final_rating_type.final_score
        context["appraisal_confirmation_forms"] = self.get_appraisal_confirmation_form(None)
        context["appraisee_personal_attr_qr"] = self.get_all_quarters_apraisee_personal_attrs()
        context["final_comment_form"] = self.get_final_comment_form(None)
        context["is_within_current_quarter"] = self.is_current_date_in_current_quarter()
        context["is_all_scored"] = self.is_all_scored()
        context["is_detail_view"] = True
        context["current_quarter"] = self.get_current_quarter_type()
        return context
    
    
    def post(self, request, *args, **kwargs):
        try:
            quarter_number = self.get_quarter_num()
            if quarter_number is None:
                raise Exception(f"AppraisalConfirmationStatus has no quarter num in request")

            form = None
            
            if quarter_number == 1:
                if "hr_request" in self.request.POST:
                    form = self.get_appraisal_confirmation_form(request.POST).get("first_quarter").get("hr_form")
                if "reviewer_request" in self.request.POST:
                    form = self.get_appraisal_confirmation_form(request.POST).get("first_quarter").get("reviewer_form")
            elif quarter_number == 2:
                if "hr_request" in self.request.POST:
                    form = self.get_appraisal_confirmation_form(request.POST).get("second_quarter").get("hr_form")
                if "reviewer_request" in self.request.POST:
                    form = self.get_appraisal_confirmation_form(request.POST).get("second_quarter").get("reviewer_form")

            elif quarter_number == 3:
                if "hr_request" in self.request.POST:
                    form = self.get_appraisal_confirmation_form(request.POST).get("third_quarter").get("hr_form")
                if "reviewer_request" in self.request.POST:
                    form = self.get_appraisal_confirmation_form(request.POST).get("third_quarter").get("reviewer_form")
            else:
                if "hr_request" in self.request.POST:
                    form = self.get_appraisal_confirmation_form(request.POST).get("fourth_quarter").get("hr_form")
                if "reviewer_request" in self.request.POST:
                    form = self.get_appraisal_confirmation_form(request.POST).get("fourth_quarter").get("reviewer_form")

            if form is None:
                raise Exception(f"request has no form, request should have 'hr_request' or 'reviewer_request'")
            
            
            if form.is_valid():
                confirmation_status = form.cleaned_data.get("confirmation_status")
                comment = form.cleaned_data.get("comment")
            
                if (confirmation_status == APPRAISAL_KRA_REVIEWER_STATUS_CHOICES[2][0]) and not comment:
                    messages.error(self.request, "Please provide a rejection reason in the comment field.")
                    return redirect(reverse("appraisal_detail", kwargs={"appraisal_id": self.kwargs.get("appraisal_id")}))
                
                obj = form.instance
                obj.save()
                
                messages.success(self.request, "confirmation status saved successfully")
        except Exception as e:
            logger.error(f"[AppraisalDetailView] confirmation status for appraisal pk: {self.kwargs.get('appraisal_id')}, failed with error: {e}")
            messages.error(request, "Something went wrong, please contact the admin")

        return redirect(reverse("appraisal_detail", kwargs={"appraisal_id": self.kwargs.get("appraisal_id")}))

    
    def get(self, request, *args, **kwargs):
        try:
            self.object = None
            appraisal_object = self.get_appraisal_obj()
            if appraisal_object is None:
                logger.warning(f"[AppraisalDetailView] get_appraisal_obj() with appraisal pk: {appraisal_object.id}, not found error")
                return redirect("object_not_found_error", object_name=slugify("Appraisal"))

        except Exception as e:
            logger.error(f"[AppraisalDetailView]  get_appraisal_obj() with appraisal pk: {appraisal_object.id}, failed with error: {e}")
            return redirect("server_error_view")
        return super().get(request, *args, **kwargs)

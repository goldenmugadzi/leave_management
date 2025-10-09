from typing import Any, Dict, List
from django.forms import BaseModelForm
from django.http import HttpResponse
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic import TemplateView
from django.urls import reverse, reverse_lazy
from django.utils.text import slugify

from django.shortcuts import redirect, render
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.http.response import HttpResponseRedirect

from ...repository.appraisal import AppraisalRepository
from ...repository.kra import AppraisalDepartmentOutputRepository, AppraisalOutPutPerformanceDimensionScoreRepository, ScoreDocumentRepository,ApprasialKraReviewerStatusRepository
from ...services.kra import AppraisalDepartmentOutputService
from ...models.kra import AppraisalOutPutPerformanceDimensionScore, ScoreDocument, APPRAISAL_KRA_REVIEWER_STATUS_CHOICES, REVIEWERS_CONFIRMATION_STATUS, AppraisalDepartmentOutput
from ...models.departmental_workplan import PERFORMANCE_INDICATOR
from ...forms.kra import AppraisalOutPutPerformanceDimensionScoreForm, ScoreDocumentForm, AppraisalDepartmentOutputReviewerStatusForm, AppraiserConfirmationForm
from ..helper import build_payload_score
from ..helper import is_within_current_quarter
from ...helpers.getters.approval import ApprovalStagesHandler
from django.core.exceptions import ValidationError
from it.users.models import GRADE_CHOICES
from loguru import logger


class AppraisalDepartmentOutputTemplateView(TemplateView):
    template_name = 'appraisal/performance_plan/appraisal_department_output.html'
    
    def get_appraisal_object(self):
        repo = AppraisalRepository()
        return repo.get_appraisal_by_pk(appraisal_id=self.kwargs.get('appraisal_id'))
    
    def get_all_appraisal_dept_output_quarters(self):
        appraisal_object = self.get_appraisal_object()
        appraisal_year = appraisal_object.created_date.year
        service_handler = AppraisalDepartmentOutputService(appraisal_department_output_repo=AppraisalDepartmentOutputRepository())
        return service_handler.fetch_quarterly(appraisal_id=appraisal_object.id, year=appraisal_year) 
    
    def appraisee_grade(self):
        user_obj = self.get_appraisal_object().user
        
        if user_obj.grade == GRADE_CHOICES[1][1]:
            return GRADE_CHOICES[1][1]
        
        if user_obj.grade == GRADE_CHOICES[2][1]:
            return "C, D, E and F"
        return ""
    
    def get_approval_stages(self):
        try:
            appraisal_object = self.get_appraisal_object()
            handler = ApprovalStagesHandler(appraisal_id=appraisal_object.id)
            return handler.get_stages_info()
        except Exception as e:
            logger.error(f"[AppraisalUpdateView] get_approval_stages for Appraisal pk: {appraisal_object.id} failed with error: {e}")
            return None    
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        appraisal_object = self.get_appraisal_object()
        appraisee_object = appraisal_object.user
        context.update(self.get_approval_stages())
        context["appraisal_dept_output_qr"] = self.get_all_appraisal_dept_output_quarters()
        context["appraisee_object"] = appraisee_object
        context["appraisal_object"] = appraisal_object
        context["is_grade_c_and_above"] = appraisee_object.grade == GRADE_CHOICES[2][0]
        context["appraisee_grade"] = self.appraisee_grade()

        return context
    
    def get(self, request, *args, **kwargs):
        try:
            appraisal_id = self.kwargs.get('appraisal_id')
            appraisal_object = self.get_appraisal_object()
            if appraisal_object is None:
                logger.warning(f"[AppraisalDepartmentOutputTemplateView] get_appraisal_object() with appraisal pk: {appraisal_id}, not found error")
                return redirect("object_not_found_error", object_name=slugify("Appraisal"))

        except Exception as e:
            logger.error(f"[AppraisalDepartmentOutputTemplateView]  get_appraisal_object() with appraisal pk: {appraisal_id}, failed with error: {e}")
            return redirect("server_error_view")
        return super().get(request, *args, **kwargs)

class AppraisalDepartmentPerformanceDimensionTemplateView(SuccessMessageMixin, UpdateView):
    model = AppraisalDepartmentOutput
    form_class = AppraisalDepartmentOutputReviewerStatusForm
    template_name = 'appraisal/performance_plan/appraisal_department_perf_dimension.html'
    success_message = 'Saved successfully'

    def get_appraisal_department_output_obj(self):
        repo = AppraisalDepartmentOutputRepository()
        return repo.get_by_id(appraisal_department_output_id=self.kwargs.get('appraisal_department_output_id'))
    
    def get_object(self, queryset = None):
        return self.get_appraisal_department_output_obj()
    
    def get_appraisee_object(self):
        dept_appraisal_output_obj = self.get_appraisal_department_output_obj()
        return dept_appraisal_output_obj.appraisal.user
    
    def get_all_perf_dimensions(self):
        repo = AppraisalOutPutPerformanceDimensionScoreRepository()
        return repo.fetch_by_department_output_id(appraisal_department_output_id=self.kwargs.get('appraisal_department_output_id'))
    
    def appraisee_grade(self):
        user_obj = self.get_appraisee_object()
        
        if user_obj.grade == GRADE_CHOICES[1][1]:
            return GRADE_CHOICES[1][1]
        
        if user_obj.grade == GRADE_CHOICES[2][1]:
            return "C, D, E and F"
        return ""
    
    def requesters(self)->Dict[str, bool]:
        appraisal_object = self.get_object().appraisal
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
    
    
    def get_appraiser_review_status_obj(self):
        repo = ApprasialKraReviewerStatusRepository()
        return repo.get_by_appraisal_department_output_id_for_appraiser(appraisal_department_output_id=self.get_object().id)

    def get_reviewer_status_obj(self):
        repo = ApprasialKraReviewerStatusRepository()
        return repo.get_by_appraisal_department_output_id_for_reviewer(appraisal_department_output_id=self.get_object().id)

    def get_hr_review_status_obj(self):
        repo = ApprasialKraReviewerStatusRepository()
        return repo.get_by_appraisal_department_output_id_for_hr(appraisal_department_output_id=self.get_object().id)

    def get_reviewer_form(self):
        obj = self.get_reviewer_status_obj()
        return AppraisalDepartmentOutputReviewerStatusForm(instance=obj)
    
    def get_appraiser_form(self):
        obj = self.get_appraiser_review_status_obj()
        return AppraisalDepartmentOutputReviewerStatusForm(instance=obj)
    
    def get_hr_form(self):
        obj = self.get_hr_review_status_obj()
        return AppraisalDepartmentOutputReviewerStatusForm(instance=obj)

    def reviewers_status_workflow(self):
        appraiser_status_review_obj = self.get_appraiser_review_status_obj()
        reviewer_status_review_obj = self.get_reviewer_status_obj()
        hr_status_review_obj = self.get_hr_review_status_obj()
        
        accept_status = APPRAISAL_KRA_REVIEWER_STATUS_CHOICES[1][0]
        is_appraiser_review_and_confirm = appraiser_status_review_obj.confirmation_status == accept_status
        is_reviewer_review_and_confirm = reviewer_status_review_obj.confirmation_status == accept_status
        is_hr_review_and_confirm = hr_status_review_obj.confirmation_status == accept_status
        
        return {
            "is_appraiser_review_and_confirm": is_appraiser_review_and_confirm,
            "is_reviewer_review_and_confirm": is_reviewer_review_and_confirm,
            "is_hr_review_and_confirm": is_hr_review_and_confirm,
        }
    
    def is_appraiser_request(self):
        if "appraiser_request" in self.request.POST:
            return True
        return False
    
    def is_reviewer_request(self):
        if "reviewer_request" in self.request.POST:
            return True
        return False
    
    def is_hr_request(self):
        if "hr_request" in self.request.POST:
            return True
        return False
    
    def is_current_date_in_current_quarter(self)->bool:
        appraisal_year_quarter_obj = self.get_object().year_quarter
        return is_within_current_quarter(year=appraisal_year_quarter_obj.year, quarter=appraisal_year_quarter_obj.quarter)
    
    def get_approval_stages(self):
        try:
            appraisal_object = self.get_appraisal_department_output_obj().appraisal
            handler = ApprovalStagesHandler(appraisal_id=appraisal_object.id)
            return handler.get_stages_info()
        except Exception as e:
            logger.error(f"[AppraisalUpdateView] get_approval_stages for Appraisal pk: {appraisal_object.id} failed with error: {e}")
            return None   
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        appraisee_object = self.get_appraisee_object()
        
        perf_dimension_qr = self.get_all_perf_dimensions()
        unscored_dimension = perf_dimension_qr.filter(is_scored=False)
        is_all_scored = False
        if not unscored_dimension.exists():
            is_all_scored = True
        context.update(self.requesters())
        context.update(self.reviewers_status_workflow())
        context.update(self.get_approval_stages())
        context["appraisee_object"] = appraisee_object
        context["department_output_obj"] = self.get_appraisal_department_output_obj().department_output
        context["appraisal_department_output_obj"] = self.get_appraisal_department_output_obj()
        context["is_grade_c_and_above"] = appraisee_object.grade == GRADE_CHOICES[2][0]
        context["performance_dimensions_qr"] = perf_dimension_qr
        context["appraisee_grade"] = self.appraisee_grade()

        context["is_within_current_quarter"] = self.is_current_date_in_current_quarter()
        context["appraiser_form"] = self.get_appraiser_form()
        context["reviewer_form"] = self.get_reviewer_form()
        context["hr_form"] = self.get_hr_form()
        context["all_scored"] = is_all_scored
        return context
    
    def reviewer_status_handler(self, form, reviewer_status_obj):
        try:
            if form.is_valid():
                confirmation_status = form.cleaned_data.get("confirmation_status")
                comment = form.cleaned_data.get("comment")
            
                if (confirmation_status == APPRAISAL_KRA_REVIEWER_STATUS_CHOICES[2][0]) and not comment:
                    messages.error(self.request, "Please provide a rejection reason in the comment field.")
                    return self.form_invalid(form)
            
                repo = ApprasialKraReviewerStatusRepository()

                return repo.update(
                    reviewer_status_obj=reviewer_status_obj,
                    confirmation_status=confirmation_status,
                    comment=comment
                )
            else:
                for field, errors in form.errors.items():
                    for err in errors:
                        messages.error(self.request, f"{field}: {err}")
        except Exception as e:
            logger.error(f"[{self.__class__.__name__}] reviewer_status_handler failed: {e}")
            messages.error(self.request, "Updating reviewer status failed, please try again")

        return HttpResponseRedirect(self.get_success_url())
    
    def form_valid(self, form):
        try:
            if self.is_appraiser_request():
                appraiser_review_status_obj = self.get_appraiser_review_status_obj()
                updated_object = self.reviewer_status_handler(form, appraiser_review_status_obj)
            elif self.is_reviewer_request():
                reviewer_status_obj = self.get_reviewer_status_obj()
                updated_object = self.reviewer_status_handler(form, reviewer_status_obj)
            elif self.is_hr_request():
                hr_review_status_object = self.get_hr_review_status_obj()
                updated_object = self.reviewer_status_handler(form, hr_review_status_object)
            else:
                raise Exception("Request not allowed, only 'appraiser_request' , 'reviewer_request' and 'hr_request' allowed")
            form.instance = updated_object
        except ValidationError as e:
            messages.error(self.request, "\n".join(e.messages))
            return super().form_invalid(form)
        except Exception as e:
            logger.error(f"[ AppraisalDepartmentPerformanceDimensionTemplateView ] form_valid with performance dimension pk-{self.kwargs.get('performance_dimension_id')}, failed with error: {e}")
            messages.error(self.request, "An unexpected error occurred, please try again")
            return super().form_invalid(form)
        return super().form_valid(form)
    
    def get(self, request, *args, **kwargs):
        try:
            appraisal_department_output_obj = self.get_appraisal_department_output_obj()
            appraisal_department_output_id = self.kwargs.get('appraisal_department_output_id')
            self.object = appraisal_department_output_obj
            if appraisal_department_output_obj is None:
                logger.warning(f"[AppraisalDepartmentPerformanceDimensionTemplateView] get_appraisal_department_output_obj() with appraisal_department_output pk: {appraisal_department_output_id}, not found error")
                return redirect("object_not_found_error", object_name=slugify("Department Output"))

        except Exception as e:
            logger.error(f"[AppraisalDepartmentPerformanceDimensionTemplateView]  get_appraisal_department_output_obj() with appraisal_department_output pk: {appraisal_department_output_id}, failed with error: {e}")
            return redirect("server_error_view")
        return super().get(request, *args, **kwargs)
    
    def get_success_url(self) -> str:
        """
        Redirects to the index page after successful update.
        """
        return reverse('appraisal_dept_perf_index', kwargs={"appraisal_department_output_id": self.kwargs.get('appraisal_department_output_id')})


class AppraisalDepartmentPerformanceDimensionScoreUpdateView(SuccessMessageMixin, UpdateView):
    model = AppraisalOutPutPerformanceDimensionScore
    form_class = AppraisalOutPutPerformanceDimensionScoreForm
    template_name = 'appraisal/performance_plan/score_form.html'
    success_message = 'Saved successfully'
    context_object_name = "score_form"

    def get_score_object(self):
        repo = AppraisalOutPutPerformanceDimensionScoreRepository()
        performance_dimension_id = self.kwargs.get("performance_dimension_id")
        return repo.get_by_id(pk=performance_dimension_id)

    def get_object(self, queryset=None):
        """
        Override the default get_object method to retrieve the performance_dimension object using a custom service.
        """
        obj = self.get_score_object()
        return obj
    
    def get_score_documents(self):
        repo = ScoreDocumentRepository()
        qr = repo.fetch_by_score_id(score_obj_id=self.get_object().id)
        return {"score_documents_qr": qr}
    
    def get_initial_form(self):
        return AppraisalOutPutPerformanceDimensionScoreForm(instance=self.get_object())
    
    def requesters(self)->Dict[str, bool]:
        appraisal_object = self.get_object().appraisal_department_output.appraisal
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
    
        
    def appraisee_grade(self):
        user_obj = self.get_object().appraisal_department_output.appraisal.user
        
        if user_obj.grade == GRADE_CHOICES[1][1]:
            return GRADE_CHOICES[1][1]
        
        if user_obj.grade == GRADE_CHOICES[2][1]:
            return "C, D, E and F"
        return ""
    
    def is_current_date_in_current_quarter(self)->bool:
        appraisal_year_quarter_obj = self.get_object().appraisal_department_output.year_quarter
        return is_within_current_quarter(year=appraisal_year_quarter_obj.year, quarter=appraisal_year_quarter_obj.quarter)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[self.context_object_name] = self.get_initial_form()
        score_obj = self.get_object()
        context.update(self.requesters())
        context.update(self.get_score_documents())
        
        context["is_within_current_quarter"] = self.is_current_date_in_current_quarter()
        context["score_object"] = score_obj
        context["appraisee_grade"] = self.appraisee_grade()

        return context
    
    
    
        
    def appraisee_form_handler(self, form):
        payload = build_payload_score(request=self.request, form=form, is_appraisee=True)
        repo = AppraisalOutPutPerformanceDimensionScoreRepository()
        current_score_object = self.get_object()
        
        is_scored = False
        obj = self.get_object().performance_dimension

        if obj.performance_indicator == PERFORMANCE_INDICATOR[1][1] and payload.score not in [0, 100]:
            messages.error(request=self.request, message="Quality is absolute — it’s either 100% or nothing.")
            return current_score_object
        else:
            is_scored = True
        
        if payload.score > 0 or obj.weight == 0:
            is_scored = True
            
        updated_score_object = repo.update(
                                    appraisal_perf_dimension=self.get_object(), 
                                    score=payload.score, 
                                    is_scored=is_scored, 
                                    appraiser_confirmation=current_score_object.appraiser_confirmation,
                                    comments=current_score_object.comments
                                    )
        return updated_score_object
            
        
    def form_valid(self, form):
        try:
            updated_object = self.appraisee_form_handler(form=form)
            form.instance = updated_object
        except ValidationError as e:
            messages.error(self.request, "\n".join(e.messages))
            return super().form_invalid(form)
        except Exception as e:
            logger.error(f"[ AppraisalDepartmentPerformanceDimensionScoreUpdateView ] form_valid with performance dimension pk-{self.kwargs.get('performance_dimension_id')}, failed with error: {e}")
            messages.error(self.request, "An unexpected error occurred, please try again")
            return super().form_invalid(form)
        return super().form_valid(form)

    def get(self, request, *args, **kwargs):
        try:
            score_object = self.get_object()
            self.object = score_object
            if score_object is None:
                logger.error(f"[AppraisalDepartmentPerformanceDimensionScoreUpdateView] get performance dimension pk-{self.kwargs.get('performance_dimension_id')}, Score object not found")
                return redirect("object_not_found_error", object_name=slugify("Score"))
            context = self.get_context_data(**kwargs)
            return self.render_to_response(context)
        except Exception as e:
            logger.error(f"[AppraisalDepartmentPerformanceDimensionScoreUpdateView] get performance dimension pk-{self.kwargs.get('performance_dimension_id')}, failed with error: {e}")
            return redirect("server_error_view")

    def get_success_url(self) -> str:
        """
        Redirects to the index page after successful update.
        """
        return reverse('score_view', kwargs={"performance_dimension_id": self.kwargs.get('performance_dimension_id')})

class ScoreDocumentCreateView(SuccessMessageMixin, CreateView):
    model = ScoreDocument
    form_class = ScoreDocumentForm
    template_name = 'appraisal/performance_plan/score_docs/create_update.html'
    success_message = 'Supporting document was set successfully'
    context_object_name = "score_document_form"

    def get_score_object(self):
        repo = AppraisalOutPutPerformanceDimensionScoreRepository()
        performance_dimension_id = self.kwargs.get("performance_dimension_id")
        return repo.get_by_id(pk=performance_dimension_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_create"] = True
        context[self.context_object_name] = context.get("form")
        return context

    def form_valid(self, form):
        try:
            file_name = form.cleaned_data.get('name')
            file_obj = self.request.FILES.get('documents')
            repo = ScoreDocumentRepository()
            score_doc_obj = repo.create(performance_dimension_score=self.get_score_object(), name=file_name, documents=file_obj)

            form.instance = score_doc_obj
        except ValidationError:
            return super().form_invalid(form)
        except Exception as e:
            logger.error(f"[ScoreDocumentCreateView] form_valid, failed with error: {e}")
            messages.error(self.request, f"something went wrong, please try again")
            return super().form_invalid(form)
        return super().form_valid(form)
    
    def get(self, request, *args, **kwargs):
        self.object = None
        try:
            score_object = self.get_score_object()
            if score_object is None:
                logger.error(f"[ScoreDocumentCreateView] get performance dimension pk-{self.kwargs.get('performance_dimension_id')}, Score object not found")
                return redirect("object_not_found_error", object_name=slugify("Score"))
            context = self.get_context_data(**kwargs)
            return self.render_to_response(context)
        except Exception as e:
            logger.error(f"[ScoreDocumentCreateView] get performance dimension pk-{self.kwargs.get('performance_dimension_id')}, failed with error: {e}")
            return redirect("server_error_view")
        
    def get_success_url(self) -> str:
        """
        Redirects to the index page after successful update.
        """
        return reverse('score_view', kwargs={"performance_dimension_id": self.kwargs.get('performance_dimension_id')})

class ScoreDocumentUpdateView(SuccessMessageMixin, UpdateView):
    model = ScoreDocument
    form_class = ScoreDocumentForm
    template_name = 'appraisal/performance_plan/score_docs/create_update.html'
    success_message = 'Supporting document was set successfully'
    context_object_name = "score_document_form"

    def get_score_doc_object(self):
        repo = ScoreDocumentRepository()
        score_doc_id = self.kwargs.get("score_doc_id")
        return repo.get_by_id(pk=score_doc_id)
    
    def get_object(self, queryset = ...):
        return self.get_score_doc_object()
    
    def get(self, request, *args, **kwargs):
        try:
            doc_obj = self.get_object()
            self.object = doc_obj
            if doc_obj is None:
                logger.error(f"[ScoreDocumentUpdateView] get document obj pk-{self.kwargs.get('score_doc_id')}, Score object not found")
                return redirect("object_not_found_error", object_name=slugify("Score Document"))
            context = self.get_context_data(**kwargs)
            return self.render_to_response(context)
        except Exception as e:
            logger.error(f"[ScoreDocumentUpdateView] get document obj pk-{self.kwargs.get('score_doc_id')}, failed with error: {e}")
            return redirect("server_error_view")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_create"] = False
        context[self.context_object_name] = context.get("form")
        return context

    def form_valid(self, form):
        try:
            file_name = form.cleaned_data.get('name')
            file_obj = self.request.FILES.get('documents')
            repo = ScoreDocumentRepository()
            score_doc_obj = repo.update(score_doc_obj=self.get_object(), name=file_name, file=file_obj)
 
            form.instance = score_doc_obj
        except ValidationError:
            return super().form_invalid(form)
        except Exception as e:
            logger.error(f"[ScoreDocumentUpdateView] form_valid, failed with error: {e}")
            messages.error(self.request, f"something went wrong, please try again")
            return super().form_invalid(form)
        return super().form_valid(form)
    
    def post(self, request, *args, **kwargs):
        """
        Handle POST requests: instantiate a form instance with the passed
        POST variables and then check if it's valid.
        """
        if "delete_request" in self.request.POST:
            repo = ScoreDocumentRepository()
            
            try:
                performance_dimension_id = self.get_object().performance_dimension_score.id
                repo.delete_obj(score_doc_obj=self.get_object())
                messages.success(self.request, "Supporting document deleted successfully")
            except Exception as e:
                logger.error(f"[ScoreDocumentUpdateView] deletion request failed with error: {e}")
                messages.error(self.request, "Supporting document deletion failed, please try again")
            
                
            return HttpResponseRedirect(reverse('score_view', kwargs={"performance_dimension_id": performance_dimension_id}))
        
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)
        


    def get_success_url(self) -> str:
        """
        Redirects to the index page after successful update.
        """
        return reverse('score_doc_update', kwargs={"score_doc_id": self.kwargs.get('score_doc_id')})


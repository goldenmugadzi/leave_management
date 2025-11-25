from typing import Any, Mapping
from django import forms
from django.forms import modelformset_factory
from django.forms.renderers import BaseRenderer
from django.forms.utils import ErrorList
from it.users.models import UserQualification, CostCenter, UserProfile, Designations
from ..services.user import UserProfileService
from ..repository.users import UserProfileRepository
from ..models import Appraisal, AppraisalExperience, Experience, AppraiseePersonalAttribute, AppraisalOverallComments
from ..helpers.types.kra import KraRolesType
from ..helpers.types.approval import ApprovalStageChoices


class UserQualificationForm(forms.ModelForm):
    class Meta:
        model = UserQualification
        exclude = ["created", "updated", "user"]


class CostCenterForm(forms.ModelForm):
    name = forms.ModelChoiceField(queryset=CostCenter.objects.all())

    class Meta:
        model = CostCenter
        exclude = ["id", "parent"]
        labels = {
            'name': 'Section',
        }


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ["username", "designation", "cost_center", "grade", "national_id"]


class DesignationForm(forms.ModelForm):
    class Meta:
        model = Designations
        fields = ["identifier", "chk"]


class AppraisalExperienceForm(forms.ModelForm):
    class Meta:
        model = AppraisalExperience
        fields = ['experience', 'years_of_experience', 'months_of_experience']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Get all Experience objects and create choices
        experience_choices = [(obj.id, obj.name) for obj in Experience.objects.all()]
        
        # Add placeholder option at the top
        experience_choices.insert(0, ("", "--------------------"))
        
        # Assign choices to the widget
        self.fields['experience'].widget = forms.Select(choices=experience_choices)

class AppraisalExperienceUpdateForm(forms.ModelForm):
    class Meta:
        model = AppraisalExperience
        fields = ['experience', 'years_of_experience', 'months_of_experience']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['experience'].disabled = True


def get_all_cost_center_users(user_id):
    service_handler = UserProfileService(UserProfileRepository())
    cost_center_user_qr = service_handler.fetch_cost_center_users_from_user_id(user_id=user_id)
    
    if cost_center_user_qr is None:
        cost_center_user_qr = UserProfile.objects.none()
    else:
        # exclude this user instance
        cost_center_user_qr = cost_center_user_qr.exclude(id=user_id)
    return cost_center_user_qr

def get_regional_hrs(region_id):
    repo = UserProfileRepository()
    return repo.fetch_by_region_id_hr_section(region_id=region_id)

def get_regional_users(region_id):
    repo = UserProfileRepository()
    return repo.fetch_by_region_id(region_id=region_id)



class AppraisalForm(forms.ModelForm):
    
    class Meta:
        model = Appraisal
        fields = ["appraiser", "reviewer", "hr"]
        
    def __init__(self, *args, **kwargs):
        appraisee_id = kwargs.pop("appraisee_id", None)
        super().__init__(*args, **kwargs)
        
        if appraisee_id is not None:
            cost_center_user_qr = get_all_cost_center_users(user_id=appraisee_id)
            self.fields["appraiser"].queryset = cost_center_user_qr
        
        self.fields["appraiser"].required = True
        self.fields["reviewer"].required = False
        self.fields["reviewer"].disabled = True
        self.fields['hr'].disabled = True
        self.fields['hr'].required = False
        

class AppraisalOverallCommentForm(forms.ModelForm):
    class Meta:
        model = AppraisalOverallComments
        fields = ["appraiser_comment"]

        
    def __init__(self, *args, **kwargs):
        is_appraiser = kwargs.pop("is_appraiser", False)
        super().__init__(*args, **kwargs)

        if not is_appraiser:
            self.fields['appraiser_comment'].disabled = True

class AppraisalUpdateForm(forms.ModelForm):
        
    class Meta:
        model = Appraisal
        fields = ["appraiser", "reviewer", "hr"]
        
    def __init__(self, *args, **kwargs):
        appraisee_id = kwargs.pop("appraisee_id", None)
        appraiser_id = kwargs.pop("appraiser_id", None)
        appraisal_reviewer_id = kwargs.pop("appraisal_reviewer_id", None)
        appraisal_appraisee_id = kwargs.pop("appraisal_appraisee_id", None)
        super().__init__(*args, **kwargs)
        
        if appraisee_id:
            cost_center_user_qr = get_all_cost_center_users(user_id=appraisee_id)
            
            if appraisal_reviewer_id is not None:
                self.fields["appraiser"].queryset = cost_center_user_qr.exclude(id=appraisal_reviewer_id) #exclude reviewer
            self.fields['reviewer'].disabled = True
            self.fields["reviewer"].required = False
            
            self.fields["hr"].required = False
            self.fields["hr"].disabled = True
        elif appraiser_id:
            cost_center_user_qr = get_all_cost_center_users(user_id=appraiser_id)

            user_obj = cost_center_user_qr.first()
            regional_user_qr = get_regional_users(region_id=user_obj.region.id)
            
            self.fields["hr"].queryset = get_regional_hrs(region_id=user_obj.region.id)
            self.fields["reviewer"].queryset = regional_user_qr.exclude(id=appraisal_appraisee_id) #exclude appraisee
            self.fields['appraiser'].disabled = True
        else:
            self.fields['appraiser'].disabled = True
            self.fields['reviewer'].disabled = True
            self.fields["hr"].disabled = True
        

class ExperienceForm(forms.ModelForm):
    class Meta:
        model = Experience
        fields = ["name"]

class AppraiseePersonalAttributeForm(forms.ModelForm):
    class Meta:
        model = AppraiseePersonalAttribute
        exclude = ["created", "updated", "appraisal", "quarter"]
        
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['personal_attribute'].disabled = True
        for field_name in ['excellent', 'very_good', 'satisfactory', 'requires_improvement', 'unsatisfactory']:
            self.fields[field_name].widget.attrs.update({
                'class': 'rating-checkbox'
            })

class ApprovalStageFilterForm(forms.Form):
    
    approval_stage_filter = forms.ChoiceField(
        choices=ApprovalStageChoices.choices(),
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
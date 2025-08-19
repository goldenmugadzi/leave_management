from typing import Any, Mapping
from django import forms
from django.forms import modelformset_factory
from django.forms.renderers import BaseRenderer
from django.forms.utils import ErrorList
from it.users.models import UserQualification, CostCenter, UserProfile, Designations
from ..models import Appraisal, AppraisalExperience, Experience, AppraiseePersonalAttribute
from ..helpers.types.kra import KraRolesType


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

class AppraisalForm(forms.ModelForm):
    
    class Meta:
        model = Appraisal
        fields = ["appraiser", "reviewer"]
        
    def __init__(self, *args, **kwargs):
        appraisee_id = kwargs.pop("appraisee_id", None)
        super().__init__(*args, **kwargs)
        
        if appraisee_id is not None:
            qr_exclude_appraisee = UserProfile.objects.exclude(id=appraisee_id)
            self.fields["appraiser"].queryset = qr_exclude_appraisee
        
        self.fields["appraiser"].required = True
        self.fields["reviewer"].required = False
        self.fields['reviewer'].disabled = True
        
class AppraisalOverallCommentForm(forms.ModelForm):
    class Meta:
        model = Appraisal
        fields = ["appraiser_comment", "reviewer_comment"]
        
    def __init__(self, *args, **kwargs):
        is_appraiser = kwargs.pop("is_appraiser", False)
        is_reviewer = kwargs.pop("is_reviewer", False)
        super().__init__(*args, **kwargs)
        
        if is_appraiser:
            self.fields['reviewer_comment'].disabled = True
            
        if is_reviewer:
            self.fields['appraiser_comment'].disabled = True
        
        if not is_appraiser and not is_reviewer:
            self.fields['appraiser_comment'].disabled = True
            self.fields['reviewer_comment'].disabled = True

class AppraisalUpdateForm(forms.ModelForm):
        
    class Meta:
        model = Appraisal
        fields = ["appraiser", "reviewer"]
        
    def __init__(self, *args, **kwargs):
        appraisee_id = kwargs.pop("appraisee_id", None)
        appraiser_id = kwargs.pop("appraiser_id", None)
        appraisal_appraisee_id = kwargs.pop("appraisal_appraisee_id", None)
        super().__init__(*args, **kwargs)
        
        if appraisee_id:
            qr_exclude_appraisee = UserProfile.objects.exclude(id=appraisee_id)
            self.fields["appraiser"].queryset = qr_exclude_appraisee
            self.fields['reviewer'].disabled = True
            self.fields["reviewer"].required = False
        elif appraiser_id:
            qr_exclude_appraiser = UserProfile.objects.exclude(id=appraiser_id).exclude(id=appraisal_appraisee_id)
            self.fields["reviewer"].queryset = qr_exclude_appraiser
            self.fields['appraiser'].disabled = True
        else:
            self.fields['appraiser'].disabled = True
            self.fields['reviewer'].disabled = True
        

class ExperienceForm(forms.ModelForm):
    class Meta:
        model = Experience
        fields = ["name"]

class AppraiseePersonalAttributeForm(forms.ModelForm):
    class Meta:
        model = AppraiseePersonalAttribute
        exclude = ["created", "updated", "appraisal"]
        
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['personal_attribute'].disabled = True
        for field_name in ['excellent', 'very_good', 'satisfactory', 'requires_improvement', 'unsatisfactory']:
            self.fields[field_name].widget.attrs.update({
                'class': 'rating-checkbox'
            })

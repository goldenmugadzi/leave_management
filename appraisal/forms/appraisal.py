from typing import Any, Mapping
from django import forms
from django.forms import modelformset_factory
from django.forms.renderers import BaseRenderer
from django.forms.utils import ErrorList
from it.users.models import UserQualification, CostCenter, UserProfile, Designations
from ..models import Appraisal, AppraisalExperience, Experience
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
    appraiser = forms.ModelChoiceField(
        queryset=UserProfile.objects.filter(roles__role=KraRolesType.appraiser.value),
        widget=forms.Select(attrs={
            'id': 'id_appraiser',  # Add an ID for targeting with JavaScript
        }),
        required=True
    )
    reviewer = forms.ModelChoiceField(
        queryset=UserProfile.objects.filter(roles__role=KraRolesType.reviewer.value),
        widget=forms.Select(attrs={
            'id': 'id_reviewer',  # Add an ID for targeting with JavaScript
        }),
        required=False
    )
    
    class Meta:
        model = Appraisal
        fields = ["appraiser", "reviewer"]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['reviewer'].disabled = True
        
class AppraisalUpdateForm(forms.ModelForm):
    appraiser = forms.ModelChoiceField(
        queryset=UserProfile.objects.filter(roles__role=KraRolesType.appraiser.value),
        widget=forms.Select(attrs={
            'id': 'id_appraiser',  # Add an ID for targeting with JavaScript
        }),
        required=True
    )
    reviewer = forms.ModelChoiceField(
        queryset=UserProfile.objects.filter(roles__role=KraRolesType.reviewer.value),
        widget=forms.Select(attrs={
            'id': 'id_reviewer',  # Add an ID for targeting with JavaScript
        }),
        required=False
    )
    
    class Meta:
        model = Appraisal
        fields = ["appraiser", "reviewer"]
        
    def __init__(self, *args, **kwargs):
        role = kwargs.pop("role", None)
        super().__init__(*args, **kwargs)
        match role:
            case KraRolesType.appraisee.value:
                self.fields['reviewer'].disabled = True
            case KraRolesType.appraiser.value:
                self.fields['appraiser'].disabled = True
            case None:
                self.fields['appraiser'].disabled = True
                self.fields['reviewer'].disabled = True
                
    def clean(self):
        cleaned_data = super().clean()
        role = self.initial.get("role")
        
        # Ensure reviewer is set before marking as accepted
        if role == KraRolesType.appraiser.value and not cleaned_data.get("reviewer"):
            raise forms.ValidationError("A reviewer must be assigned before accepting the appraisal.")
        
        return cleaned_data
        

class ExperienceForm(forms.ModelForm):
    class Meta:
        model = Experience
        fields = ["name"]

from typing import Any, Mapping
from django import forms
from django.forms import modelformset_factory
from django.forms.renderers import BaseRenderer
from django.forms.utils import ErrorList
from it.users.models import UserQualification, CostCenter, UserProfile, Designations
from ..models import Appraisal, AppraisalExperience, Experience


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
        fields = ["appraiser"]

    appraiser = forms.ModelChoiceField(
        queryset=UserProfile.objects.all(),
        widget=forms.Select(attrs={
            'id': 'id_appraiser',  # Add an ID for targeting with JavaScript
            'class': 'bg-white border border-gray-300 rounded-lg py-2 px-4 block w-full focus:ring-blue-500 focus:border-blue-500 text-gray-700'
        }),
        required=True
    )

class ExperienceForm(forms.ModelForm):
    class Meta:
        model = Experience
        fields = ["name"]

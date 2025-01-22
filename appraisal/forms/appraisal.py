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

class AppraisalForm(forms.ModelForm):
    class Meta:
        model = Appraisal
        fields = ["appraiser"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            if field_name == 'appraiser':
                field.widget.attrs.update({
                    'class': "select2 block w-full rounded-md border-0 py-1.5 text-gray-900 "
                                "shadow-sm ring-1 ring-inset ring-gray-300 "
                                "placeholder:text-blue-400 focus:ring-2 focus:ring-inset "
                                "focus:ring-indigo-600 sm:text-sm sm:leading-6", })

class ExperienceForm(forms.ModelForm):
    class Meta:
        model = Experience
        fields = ["name"]

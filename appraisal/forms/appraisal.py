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
        fields = ["username", "designation", "cost_center"]
        
class DesignationForm(forms.ModelForm):
    class Meta:
        model = Designations
        fields = ["identifier", "chk"]
        
class AppraisalExperienceForm(forms.ModelForm):
    class Meta:
        model = AppraisalExperience
        fields = ['experience', 'years_of_experience', 'months_of_experience']
        
        
class AppraisalForm(forms.ModelForm):
    
    class Meta:
        model = Appraisal
        fields = []
        
class ExperienceForm(forms.ModelForm):
    class Meta:
        model = Experience
        fields = ["name"]
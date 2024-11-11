from django import forms
from it.users.models import UserQualification, CostCenter, UserProfile, Designations
from ..models import Appraisal

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
        
class AppraisalForm(forms.ModelForm):
    
    class Meta:
        model = Appraisal
        fields = []
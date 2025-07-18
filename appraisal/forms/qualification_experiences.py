from django import forms
from it.users.models import UserExperience, UserQualification

class UserExperienceForm(forms.ModelForm):
    class Meta:
        model = UserExperience
        fields = ["name", "experience_from", "experience_to"]
        
class UserQualificationForm(forms.ModelForm):
    class Meta:
        model = UserQualification
        fields = ["name", "file"]

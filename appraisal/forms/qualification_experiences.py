from django import forms
from it.users.models import UserExperience, UserQualification

class UserExperienceForm(forms.ModelForm):
    class Meta:
        model = UserExperience
        fields = ["name", "experience_from", "experience_to"]
        widgets = {
            'experience_from': forms.TextInput(attrs={
                'class': 'datepicker',
                'placeholder': 'Select start date'
            }),
            'experience_to': forms.TextInput(attrs={
                'class': 'datepicker',
                'placeholder': 'Select end date'
            }),
        }
        
class UserQualificationForm(forms.ModelForm):
    class Meta:
        model = UserQualification
        fields = ["name", "file"]
        

from django import forms
from it.users.models import UserExperience, UserQualification
from django.core.exceptions import ValidationError
import os
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
        fields = ["name", "description", "file"]
        
def validate_excel_file(value):
    valid_extensions = ['.xls', '.xlsx']
    ext = os.path.splitext(value.name)[1]
    if ext.lower() not in valid_extensions:
        raise ValidationError("Only Excel files (.xls, .xlsx) are allowed.")

class UserQualificationsUploadForm(forms.Form):
    qualifications_file = forms.FileField(
        validators=[validate_excel_file],
        help_text="Upload an Excel file (.xls or .xlsx)."
        
    )
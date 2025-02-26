from django import forms
from ..models import YearQuarter, KeyResultArea, Activity, TargetScore, AppraisalKra
from ..helpers.types.kra import RoleFilterChoices
from datetime import datetime


class YearQuarterForm(forms.ModelForm):
    class Meta:
        model = YearQuarter
        fields = ["year", "quarter"]

class KraCreateForm(forms.ModelForm):
    class Meta:
        model = KeyResultArea
        exclude = ["id", "created_date", "updated"]
          
class ActivityCreateForm(forms.ModelForm):
    class Meta:
        model = Activity
        exclude = ["id", "created_date", "updated", "appraisal_kra"]
        
            
class TargetScoreForm(forms.ModelForm):
    class Meta:
        model = TargetScore
        exclude = ["id", "created_date", "updated", "target", "is_scored"]

class AppraisalRoleFilterForm(forms.Form):
    
    role_filter = forms.ChoiceField(
        choices=RoleFilterChoices.choices(),
        label="Role Filter",
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    
class AppraisalKraForm(forms.ModelForm):
    class Meta:
        model = AppraisalKra
        exclude = ["id", "created_date", "updated"]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current_year = datetime.now().year
        self.fields['quarter'].queryset = YearQuarter.objects.filter(year=current_year)      


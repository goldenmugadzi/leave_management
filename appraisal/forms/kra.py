from django import forms
from ..models import YearQuarter, KeyResultArea, Activity, TargetScore, AppraisalKra, AppraisalKraReviewerStatus, PerformanceDimension, ScoreDocument
from ..helpers.types.kra import RoleFilterChoices
from it.users.models import UserProfile
from datetime import datetime


class YearQuarterForm(forms.ModelForm):
    class Meta:
        model = YearQuarter
        fields = ["year", "quarter"]

class KraCreateForm(forms.ModelForm):
    class Meta:
        model = KeyResultArea
        exclude = ["id", "created_date", "updated", "designation"]
          
class ActivityCreateForm(forms.ModelForm):
    assigned_user = forms.ModelChoiceField(
        queryset=UserProfile.objects.all(), 
        required=False
    )
    class Meta:
        model = Activity
        exclude = ["id", "created_date", "updated", "appraisal_kra"]
        

class ScoreDocumentForm(forms.ModelForm):
    class Meta:
        model = ScoreDocument
        exclude = ["id", "target_score"]

class TargetScoreForm(forms.ModelForm):
    class Meta:
        model = TargetScore
        exclude = ["id", "created_date", "updated", "performance_dimension"]


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
        designation_id = kwargs.pop("designation_id", None)
        super().__init__(*args, **kwargs)
        current_year = datetime.now().year
        self.fields['quarter'].queryset = YearQuarter.objects.filter(year=current_year) 
        self.fields["key_result_area"].queryset =  KeyResultArea.objects.filter(designation__id=designation_id)
        
class AppraisalKraReviewerStatusForm(forms.ModelForm):
    class Meta:
        model = AppraisalKraReviewerStatus
        exclude = ["id", "created_date", "updated", "appraisal_kra"]
        
class PerformanceDimensionForm(forms.ModelForm):
    class Meta:
        model = PerformanceDimension
        exclude = ["id", "created_date", "updated", "activity", "is_applicable"]
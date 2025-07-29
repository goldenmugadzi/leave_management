from django import forms
from ..models import YearQuarter, KeyResultArea, ScoreDocument, KeyResultAreaOutCome, AppraisalOutPutPerformanceDimensionScore
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
        exclude = ["id", "created_date", "updated", "created_by", "updated_by"]
class KraOutComeCreateForm(forms.ModelForm):
    class Meta:
        model = KeyResultAreaOutCome
        exclude = ["id", "created_date", "updated", "key_result_area"]
          

class ScoreDocumentForm(forms.ModelForm):
    class Meta:
        model = ScoreDocument
        exclude = ["id", "target_score", "performance_dimension_score"]


class AppraisalRoleFilterForm(forms.Form):
    
    role_filter = forms.ChoiceField(
        choices=RoleFilterChoices.choices(),
        label="Role Filter",
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    
class AppraisalOutPutPerformanceDimensionScoreForm(forms.ModelForm):
    class Meta:
        model = AppraisalOutPutPerformanceDimensionScore
        fields = ["score", "comments", "appraiser_confirmation"]
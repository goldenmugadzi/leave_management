from django import forms
from ..models import YearQuarter, KeyResultArea, Activity, Target, TargetScore
from ..helpers.types.kra import RoleFilterChoices
from datetime import datetime


class YearQuarterForm(forms.ModelForm):
    class Meta:
        model = YearQuarter
        fields = ["year", "quarter"]

class KraCreateForm(forms.ModelForm):
    class Meta:
        model = KeyResultArea
        exclude = ["id", "created_date", "updated", "created_by"]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current_year = datetime.now().year
        self.fields['quarter'].queryset = YearQuarter.objects.filter(year=current_year)      
class ActivityCreateForm(forms.ModelForm):
    class Meta:
        model = Activity
        exclude = ["id", "created_date", "updated", "kra"]
        
class TargetCreateForm(forms.ModelForm):
    class Meta:
        model = Target
        exclude = ["id", "created_date", "updated", "activity"]
    
    def __init__(self, *args, **kwargs):
        is_grade_c = kwargs.pop("is_above_grade_c", None)
        is_appraisee = kwargs.pop("is_appraisee", None)
        super().__init__(*args, **kwargs)

        if not is_grade_c:
            self.fields["metric_type"].disabled = True
        
        if is_appraisee == True:
            self.fields["metric_type"].disabled = True
            self.fields["name"].disabled = True
            self.fields["weight"].disabled = True
            self.fields["agreed_target"].disabled = True
            self.fields["allowable_variance"].disabled = True
            self.fields["unit"].disabled = True
            
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
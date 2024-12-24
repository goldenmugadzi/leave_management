from django import forms
from ..models import YearQuarter, KeyResultArea, Activity, Target

class YearQuarterForm(forms.ModelForm):
    class Meta:
        model = YearQuarter
        fields = ["year", "quarter"]

class KraCreateForm(forms.ModelForm):
    class Meta:
        model = KeyResultArea
        exclude = ["id", "created_date", "updated", "created_by"]
        
class ActivityCreateForm(forms.ModelForm):
    class Meta:
        model = Activity
        exclude = ["id", "created_date", "updated", "kra"]
        
class TargetCreateForm(forms.ModelForm):
    class Meta:
        model = Target
        exclude = ["id", "created_date", "updated", "activity"]
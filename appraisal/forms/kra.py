from django import forms
from ..models import YearQuarter, KeyResultArea

class YearQuarterForm(forms.ModelForm):
    class Meta:
        model = YearQuarter
        fields = ["year", "quarter"]

class KraCreateForm(forms.ModelForm):
    class Meta:
        model = KeyResultArea
        exclude = ["id", "created_date", "updated"]
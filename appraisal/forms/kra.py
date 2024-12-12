from django import forms
from ..models import YearQuarter

class YearQuarterForm(forms.ModelForm):
    class Meta:
        model = YearQuarter
        fields = ["year", "quarter"]

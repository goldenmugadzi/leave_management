from django import forms
from .models import Fault

class FaultForm(forms.ModelForm):
    class Meta:
        model = Fault
        fields = ['description', 'depot']
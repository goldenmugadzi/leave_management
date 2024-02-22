from django import forms
from .models import MeterToken

class MeterTokenForm(forms.ModelForm):
    reason = forms.CharField(widget=forms.TextInput(attrs={'class': ' rounded bg-white form-control'}))
    class Meta:
        model = MeterToken
        fields = '__all__'

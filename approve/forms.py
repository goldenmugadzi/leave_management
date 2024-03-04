from django import forms
from .models import Workflow, Step

class WorkflowForm(forms.ModelForm):
    number_of_steps = forms.IntegerField(widget=forms.NumberInput(attrs={'class': 'rounded bg-white form-control'}))
    class Meta:
        model = Workflow
        fields = ['name', 'application']

class StepForm(forms.ModelForm):
    class Meta:
        model = Step
        fields = ['approver']
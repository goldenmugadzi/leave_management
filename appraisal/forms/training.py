from django import forms
from ..models import InterventionStrategy, TrainingAndDevelopment

class CompetencyForm(forms.Form):
    required_competency = forms.CharField(max_length=500, required=False)
    competency_gap = forms.CharField(max_length=500, required=False)
    
class InterventionStrategyForm(forms.ModelForm):
    class Meta:
        model = InterventionStrategy
        fields = ["description", "category"]
        
class ActionsForm(forms.ModelForm):
    class Meta:
        model = TrainingAndDevelopment
        fields = ["action_recommended", "action_taken"]
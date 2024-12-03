from django import forms
from ..models import PerformanceProgressReview, PerformanceProgressStrength, PerformanceProgressWeakness

class PerformanceReviewApprovalForm(forms.Form):
    quarter = forms.IntegerField(widget=forms.HiddenInput())
    strengths = forms.ModelMultipleChoiceField(
        queryset=PerformanceProgressStrength.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    areas_of_weaknesses = forms.ModelMultipleChoiceField(
        queryset=PerformanceProgressWeakness.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
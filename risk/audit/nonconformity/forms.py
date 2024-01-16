from django import forms
from .models import Nonconformity
from django.utils import timezone

class NonconformityForm(forms.ModelForm):
    class Meta:
        model = Nonconformity

        fields = ('created_by', 'recipient', 'attachment', 'violation_standard_reference', 'recommended_corrective_action', 'description','created_by','response', 'status', )
        exclude= ['created_by','response', 'status']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",  })
            
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'rows': '3'})
            field.label = field.label or field_name.replace('_', ' ').capitalize()
            field.label_attrs = {'class': 'block text-sm font-medium leading-6 text-gray-900'}

class NonconformityResponseForm(forms.ModelForm):
    description = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control bg-white custom-select rounded text-center'}),
        max_length=400,
        required=False,
        label='Description'
    )
    expected_completion_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control bg-white w/2-full custom-select rounded text-center'}),
        required=False,
        label='Expected Completion Date'
    )

    class Meta:
        model = Nonconformity
        fields = ['response', 'status']
        widgets = {
            'status': forms.HiddenInput(attrs={'class': 'sr-only'}),
            'response': forms.HiddenInput(attrs={'class': 'sr-only'}),
        }

        def clean_expected_completion_date(self):
            expected_completion_date = self.cleaned_data['expected_completion_date']
            today = timezone.now().date()

            if expected_completion_date is not None and expected_completion_date < today:
                raise forms.ValidationError("Expected completion date should be greater than or equal to today's date.")

            return expected_completion_date
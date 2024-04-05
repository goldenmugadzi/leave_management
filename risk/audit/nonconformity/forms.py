from django import forms
from .models import *
from django.utils import timezone
from django.core.exceptions import ValidationError
import os
from django.forms.widgets import ClearableFileInput
class ClauseForm(forms.ModelForm):
    number_of_iso_requirements = forms.IntegerField(widget=forms.NumberInput(attrs={'class': 'rounded bg-white form-control'}))
    class Meta:
        model = Clause
        fields = '__all__'
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",
            })

            field.label = field.label or field_name.replace('_', ' ').capitalize()
            field.label_attrs = {'class': 'block text-sm font-medium text-gray-900'}

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",
            })

            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'rows': '3'})
            field.label = field.label or field_name.replace('_', ' ').capitalize()
            field.label_attrs = {'class': 'block text-sm font-medium text-gray-900'}
class CustomClearableFileInput(ClearableFileInput):
    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        if value and hasattr(value, 'name'):
            file_name = os.path.basename(value.name)
            context['widget']['value'] = file_name
        return context

class NonconformityForm(forms.ModelForm):
    class Meta:
        model = Nonconformity
        fields = ( 'recipient', 'attachment', 'description', 'root_cause', 'violation_standard_reference', 'recommended_corrective_action', )
        exclude = ['created_by', 'response', 'status']
        widgets = {
            'attachment': CustomClearableFileInput
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",
            })

            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'rows': '3'})
                
            field.label = field.label or field_name.replace('_', ' ').capitalize()
            field.label_attrs = {'class': 'block text-sm font-medium leading-6 text-gray-900'}
           
class AdditionalInfoForm(forms.ModelForm):
    expected_completion_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = Nonconformity
        fields = ['plan_of_action', 'expected_completion_date']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",
            })

            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'rows': '3'})
                
            field.label = field.label or field_name.replace('_', ' ').capitalize()
            field.label_attrs = {'class': 'block text-sm font-medium leading-6 text-gray-900'}
            if field_name == 'recipient':
                choices = [(user.id, user.get_full_name()) if user.get_full_name() else (user.id, user.username) for user in User.objects.all()]
                field.choices = choices

    def clean_expected_completion_date(self):
        expected_completion_date = self.cleaned_data['expected_completion_date']
        if expected_completion_date < timezone.now().date():
            raise forms.ValidationError("The expected completion date must be now or later.")
        return expected_completion_date
        
class NonconformityResponseForm(forms.ModelForm):
    class Meta:
        model = Response
        fields = ['comment', 'status']
       
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",
            })

            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'rows': '3'})
            field.label = field.label or field_name.replace('_', ' ').capitalize()
            field.label_attrs = {'class': 'block text-sm font-medium leading-6 text-gray-900'}

        self.error_css_class = 'text-red-500'  # Add the CSS class for error messages
    
    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        comment = cleaned_data.get('comment')

        if status == 'rejected' and not comment:
            self.add_error('comment', 'A reason must be provided for rejecting the nonconformity.')

        return cleaned_data
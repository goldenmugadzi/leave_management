import datetime
from django import forms
from .models import *
from django.utils import timezone
import os
from django.forms.widgets import ClearableFileInput
class ClauseForm(forms.ModelForm):
    class Meta:
        model = Clause
        fields = '__all__'
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",
            })

         
class TopicForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ['name']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",
            })

          
class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = '__all__'
        exclude = ['topic']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",
            })

            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'rows': '3'})
         
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
        fields = ( 'recipient', 'attachment', 'description', 'root_cause', 'violation_standard_reference', 'recommended_corrective_action','findings' )
        exclude = ['created_by',  'state']
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
    expected_completion_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'min': str(datetime.date.today())}),required=False)

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

    def clean_plan_of_action(self):
        plan_of_action = self.cleaned_data.get('plan_of_action')
        expected_completion_date = self.cleaned_data.get('expected_completion_date')
        if not plan_of_action  and not expected_completion_date:
            raise forms.ValidationError("You must give a expected_completion_date for rejecting the nonconformity !")

        return plan_of_action
    def clean_expected_completion_date(self):
        expected_completion_date = self.cleaned_data.get('expected_completion_date')
        if expected_completion_date is not None and expected_completion_date < timezone.now().date():
            raise forms.ValidationError("Expected completion date cannot be in the past.")
        return expected_completion_date
class ResolveNcForm(forms.ModelForm):

    class Meta:
        model = Nonconformity
        fields = ['resolved']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():field.widget.attrs.update({'class': "inline  rounded-md border-1 border-green-900   mx-5 sm:text-lg ",})    
class CloseNcForm(forms.ModelForm):

    class Meta:
        model = Nonconformity
        fields = ['closed']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():field.widget.attrs.update({'class': "inline  rounded-md border-1 border-green-900   mx-5 sm:text-lg ",})    
   
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
  
    def clean_status(self):
        status = self.cleaned_data.get('status')
        comment = self.cleaned_data.get('comment')
        if status  and not comment:
            raise forms.ValidationError("You must give a comment for rejecting the nonconformity !")

        return status
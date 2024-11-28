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
        else:return context

class NonconformityForm(forms.ModelForm):
    class Meta:
        model = Nonconformity
        fields = "__all__"#( 'recipient', 'attachment', 'description', 'root_cause', 'violation_standard_reference', 'corrective_action','findings' )
        exclude = ['created_by',  'accepted','resolved','closed']
        widgets = {
            'attachment': CustomClearableFileInput
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",
            })
            if (field_name == 'recipient') or (field_name == 'violation_standard_reference') :
                field.widget.attrs.update({'class': "select2 block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",})
          
            if isinstance(field.widget, forms.Textarea): field.widget.attrs.update({'rows': '3'})
                
            
class AcceptanceForm(forms.ModelForm):
    expected_completion_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'min': str(datetime.date.today())}),required=False)

    class Meta:
        model = Acceptance
        fields = "__all__" 
        exclude = ['nonconformity','user','dated' ]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            if field_name ==  'resolved' :field.widget.attrs.update({'class': "block rounded-md border-0  p-4 m-3 text-gray-900 shadow-sm inline  ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",})
            elif field_name in  ['attachment','expected_completion_date'] :field.widget.attrs.update({'class': "block rounded-md border-0 w-1/2 py-2 m-3 text-gray-900 shadow-sm inline  ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",})
            else: field.widget.attrs.update({ 'class': "block w-full rounded-md border-0 my-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",})
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'rows': '3'})    

    def clean_corrective_action(self):
        corrective_action = self.cleaned_data.get('corrective_action')
        if not corrective_action:
            raise forms.ValidationError("This field is required.")
        else:return corrective_action
    def clean_cause(self):
        cause = self.cleaned_data.get('cause')
        if not cause:
            raise forms.ValidationError("This field is required.")
        else:return cause
    def clean_expected_completion_date(self):
        expected_completion_date = self.cleaned_data.get('expected_completion_date')
        if expected_completion_date is None:
            raise forms.ValidationError("This field is required.")
        if  expected_completion_date < timezone.now().date():
            raise forms.ValidationError("Expected completion date cannot be in the past.")
        else:return expected_completion_date 

class RejectionForm(forms.ModelForm):
    class Meta:
        model = Rejection
        fields = "__all__"
        exclude = ['nonconformity','user' ]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({ 'class': "block w-full rounded-md border-0 my-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",})
            if isinstance(field.widget, forms.Textarea): field.widget.attrs.update({'rows': '3'})

    def clean_rejection_reason(self):
        rejection = self.cleaned_data.get('rejection_reason')
        if len(rejection)>0 :return rejection
        else: raise forms.ValidationError("This field is required.")
        
class CloseNcForm(forms.ModelForm):

    class Meta:
        model = Nonconformity
        fields = ['closed']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():field.widget.attrs.update({'class': "inline  rounded-md border-1 border-green-900   mx-5 sm:text-lg ",})    
    
class ResolveNcForm(forms.ModelForm):
    resolved_on = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'max': str(datetime.date.today())}),required=False)

    class Meta:
        model = Resolution
        fields = "__all__"
        exclude = ['nonconformity','user','dated' ]


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():field.widget.attrs.update({'class': "inline  rounded-md border-1 border-green-900   mx-5 sm:text-lg ",})    
   

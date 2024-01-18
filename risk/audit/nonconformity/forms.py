from django import forms
from .models import *
from django.utils import timezone

class NonconformityForm(forms.ModelForm):
    class Meta:
        model = Nonconformity

        fields = ('created_by', 'recipient', 'attachment', 'violation_standard_reference', 'recommended_corrective_action', 'description','created_by', )
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
    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        comment = cleaned_data.get('comment')

        if status == 'reject' and not comment:
            raise forms.ValidationError("Comment is required for  rejection.")
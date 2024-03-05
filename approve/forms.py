from django import forms
from .models import *

class WorkflowCreateForm(forms.ModelForm):
    number_of_steps = forms.IntegerField(widget=forms.NumberInput(attrs={'class': 'rounded bg-white form-control'}))
    class Meta:
        model = Workflow
        fields = ['name', 'application']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",
            })

            field.label = field.label or field_name.replace('_', ' ').capitalize()
            field.label_attrs = {'class': 'block text-sm font-medium text-gray-900'}
   
class WorkflowUpdateForm(forms.ModelForm):
    class Meta:
        model = Workflow
        fields = "__all__" # ['name', 'application']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",
            })

            field.label = field.label or field_name.replace('_', ' ').capitalize()
            field.label_attrs = {'class': 'block text-sm font-medium text-gray-900'}

class SaveStepForm(forms.ModelForm):
    class Meta:
        model = Step
        fields = '__all__'


class StepForm(forms.ModelForm):
    class Meta:
        model = Step
        fields = ['approver','to']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",
            })

            field.label = field.label or field_name.replace('_', ' ').capitalize()
            field.label_attrs = {'class': 'block text-sm font-medium text-gray-900'}

class ApprovalForm(forms.ModelForm):
    class Meta:
        model = Approval
        fields = "__all__"
        exclude =('step', 'user', 'process',  )
        
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
    def clean(self):
        cleaned_data = super().clean()
        approved = cleaned_data.get('approved')
        comment = cleaned_data.get('comment')

        if approved == 'Rejected' and not comment:
            self.add_error('comment', 'A reason must be provided for rejecting the nonconformity.')

        return cleaned_data
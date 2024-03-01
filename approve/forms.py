from django import forms
from .models import Workflow, Step

class WorkflowCreateForm(forms.ModelForm):
    number_of_steps = forms.IntegerField(widget=forms.NumberInput(attrs={'class': 'rounded bg-white form-control'}))
    class Meta:
        model = Workflow
        fields = ['name', 'application']

class WorkflowUpdateForm(forms.ModelForm):
    class Meta:
        model = Workflow
        fields = "__all__" # ['name', 'application']

class StepForm(forms.ModelForm):
    class Meta:
        model = Step
        fields = ['approver']

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
           

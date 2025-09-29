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

         

class ApprovalForm(forms.ModelForm):
    APPROVAL_CHOICES = [
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    approved = forms.ChoiceField(
        choices=APPROVAL_CHOICES,
        widget=forms.HiddenInput(),  # Hidden since we use button values
        required=True
    )

    comment = forms.CharField(
        widget=forms.Textarea(attrs={
            'placeholder': 'Please provide comments for your decision. Comments are required for rejections.',
            'rows': 4
        }),
        required=False,  # We'll validate this in clean() method based on approval status
        help_text='Comments are required when rejecting items.'
    )

    class Meta:
        model = Approval
        fields = ['approved', 'comment']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",
            })
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'rows': '4'})

    def clean(self):
        cleaned_data = super().clean()
        approved = cleaned_data.get('approved')
        comment = cleaned_data.get('comment')

        if approved == 'Rejected':
            if not comment or not comment.strip():
                self.add_error('comment', 'A comment must be provided when rejecting a petty cash request.')

        return cleaned_data
from django import forms
from .models import *


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = "__all__"
        exclude = ['id']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset "
                         "ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 "
                         "sm:text-sm sm:leading-6",
            })

            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'rows': '3'})


class BulkUpdateCommitteeForm(forms.Form):
    """Form to bulk update committee members for multiple CS records"""
    cs_ids = forms.CharField(
        label='CS IDs (comma-separated)',
        widget=forms.Textarea(attrs={
            'rows': 5,
            'placeholder': 'Enter CS IDs separated by commas (e.g., cs001, cs002, cs003)',
            'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6'
        }),
        help_text='Enter one or more CS IDs separated by commas'
    )
    
    procurement_user_id = forms.IntegerField(
        label='Procurement User ID',
        initial=155,
        widget=forms.NumberInput(attrs={
            'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6'
        })
    )
    procurement_committee_name = forms.CharField(
        label='Procurement Committee Name',
        max_length=100,
        initial='ze233366',
        widget=forms.TextInput(attrs={
            'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6'
        })
    )
    
    user_user_id = forms.IntegerField(
        label='User Member ID',
        initial=206,
        widget=forms.NumberInput(attrs={
            'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6'
        })
    )
    user_committee_name = forms.CharField(
        label='User Committee Name',
        max_length=100,
        initial='ze2439738',
        widget=forms.TextInput(attrs={
            'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6'
        })
    )
    
    finance_user_id = forms.IntegerField(
        label='Finance User ID',
        initial=665,
        widget=forms.NumberInput(attrs={
            'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6'
        })
    )
    finance_committee_name = forms.CharField(
        label='Finance Committee Name',
        max_length=100,
        initial='ze325058',
        widget=forms.TextInput(attrs={
            'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6'
        })
    )
    
    chairman_user_id = forms.IntegerField(
        label='Chairman User ID',
        initial=401,
        widget=forms.NumberInput(attrs={
            'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6'
        })
    )
    chairman_committee_name = forms.CharField(
        label='Chairman Committee Name',
        max_length=100,
        initial='ze278610',
        widget=forms.TextInput(attrs={
            'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6'
        })
    )
    
    def clean_cs_ids(self):
        """Parse and validate CS IDs"""
        cs_ids_str = self.cleaned_data.get('cs_ids', '')
        cs_ids = [cs_id.strip() for cs_id in cs_ids_str.split(',') if cs_id.strip()]
        
        if not cs_ids:
            raise forms.ValidationError('Please enter at least one CS ID')
        
        return cs_ids


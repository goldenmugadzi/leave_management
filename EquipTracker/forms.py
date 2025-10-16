from django import forms
from .models import *
from it.users.models import Sections, Substation
from django.forms import ModelForm, DateInput
from django.forms import modelformset_factory
import datetime

FIELD_CSS_CLASSES = "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
class EquipmentForm(ModelForm):
    class Meta:
        model = Equipment
        fields = ['type_of_equipment']
        widgets = {
            'type_of_equipment': forms.Select(attrs={'class': 'form-control'}),
        }
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': FIELD_CSS_CLASSES})
            classes = FIELD_CSS_CLASSES
            classes += ' select2' 
            field.widget.attrs.update({'class': classes})
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'rows': '3'})
 
class EquipmentChangeForm(ModelForm):
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'max': str(datetime.date.today())}),required=False)
    class Meta:
        model = EquipmentChange
        fields = "__all__"
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': FIELD_CSS_CLASSES})
            classes = FIELD_CSS_CLASSES
            if field_name in ['substation','district','equipment','section']:
                classes += ' select2' 
            field.widget.attrs.update({'class': classes})
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'rows': '3'})
 
        if user and hasattr(user, 'region'):
            self.fields['substation'].queryset = Substation.objects.filter(region=user.region)
            self.fields['district'].queryset = Districts.objects.filter(region_id=str(user.region.id))
            self.fields['section'].queryset = Sections.objects.filter(region_id=str(user.region.id))

class EquipmentParticularsForm(forms.ModelForm):
    class Meta:
        model = EquipmentParticulars
        fields = ['make', 'serial_number', 'kva_or_ampere_rating', 'voltage_rating', 'action_taken']
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': FIELD_CSS_CLASSES})
            classes = FIELD_CSS_CLASSES
            if field_name in ['substation','district','equipment','section']:
                classes += ' select2' 
            field.widget.attrs.update({'class': classes})
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'rows': '3'})
 
EquipmentParticularsFormSet = modelformset_factory(EquipmentParticulars,
    form=EquipmentParticularsForm,
    extra=2,  # Number of extra empty forms to display
    can_delete=True  # Allow deletion of forms if necessary
)

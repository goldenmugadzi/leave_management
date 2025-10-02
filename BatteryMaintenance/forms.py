from django import forms
from django.forms.models import inlineformset_factory
from .models import BatteryInstallation, Cell, Substation
from it.users.models import Regions, Districts, Depots

# Shared Tailwind-style class
FIELD_CSS_CLASSES = "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"

class BatteryInstallationForm(forms.ModelForm):  
    class Meta:
        model = BatteryInstallation
        exclude = [
            'volts_high',
            'volts_low',
            'volts_avg',
            'sg_high',
            'sg_low',
            'sg_avg',
            'equipment_tracker'
        ]
        
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': FIELD_CSS_CLASSES})
            classes = FIELD_CSS_CLASSES
            if field_name in ['substation']:
                classes += ' select2'  # Add select2 for dropdowns
            field.widget.attrs.update({'class': classes})
            if isinstance(field.widget, forms.Textarea):field.widget.attrs.update({'rows': '3'})
            
        if user and hasattr(user, 'region'):
            self.fields['substation'].queryset = Substation.objects.filter(region=user.region)


class CellForm(forms.ModelForm):
    class Meta:
        model = Cell
        fields = ['specific_gravity', 'voltage']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': FIELD_CSS_CLASSES})
class SubstationForm(forms.ModelForm):
    class Meta:
        model = Substation
        fields = ['name', 'region', 'district', 'depot']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            classes = FIELD_CSS_CLASSES
            if field_name in ['region', 'district', 'depot']:
                classes += ' select2'  # Add select2 for dropdowns
            field.widget.attrs.update({'class': classes})
            field.required = False  # Make all fields optional in the form

            self.fields['region'].queryset = Regions.objects.filter(id=user.region.id)
            self.fields['district'].queryset = Districts.objects.filter(region_id=user.region.id)
            self.fields['depot'].queryset = Depots.objects.filter(region_id=user.region.id)


CellFormSet = inlineformset_factory(
    BatteryInstallation,
    Cell,
    form=CellForm,
    fields=['specific_gravity', 'voltage'],
    extra=5,
    can_delete=False
)
CellFormSet1 = inlineformset_factory(
    BatteryInstallation,
    Cell,
    form=CellForm,
    fields=['specific_gravity', 'voltage'],
    extra=0,
    can_delete=False
)
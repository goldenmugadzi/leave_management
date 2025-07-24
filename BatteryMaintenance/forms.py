# forms.py

from django import forms
from django.forms.models import inlineformset_factory
from .models import BatteryInstallation, Cell

# Shared Tailwind-style class
FIELD_CSS_CLASSES = "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"

class BatteryInstallationForm(forms.ModelForm):  
    class Meta:
        model = BatteryInstallation
        fields = [
            'cost_center', 'site_name', 'battery_name', 'cell_type',
            'cell_quantity', 'plates_per_cell', 'battery_application'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': FIELD_CSS_CLASSES})
            if field_name == 'cost_center':
                field.widget.attrs['class'] += ' select2'

class CellForm(forms.ModelForm):
    class Meta:
        model = Cell
        fields = [ 'specific_gravity', 'voltage']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            
            field.widget.attrs.update({'class': FIELD_CSS_CLASSES})


# Create inline formset using custom CellForm
CellFormSet = inlineformset_factory(
    BatteryInstallation,
    Cell,
    form=CellForm,
    fields=[ 'specific_gravity', 'voltage'],
    extra=5,
    can_delete=False
)

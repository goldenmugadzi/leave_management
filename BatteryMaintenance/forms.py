from django import forms
from django.forms.models import inlineformset_factory
from .models import BatteryInstallation, Cell, Substation, Regions, Districts, Depots

# Shared Tailwind-style class
FIELD_CSS_CLASSES = "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"

class BatteryInstallationForm(forms.ModelForm):  
   
    class Meta:
        model = BatteryInstallation
        fields = [
            'substation', 'battery_name', 'cell_type',
            'cell_quantity', 'plates_per_cell', 'battery_application'
        ]
        
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': FIELD_CSS_CLASSES})
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
        for field in self.fields.values():
            field.widget.attrs.update({'class': FIELD_CSS_CLASSES})
            if hasattr(self, 'user') and hasattr(self.user, 'region'):
                self.fields['region'].queryset = Regions.objects.filter(id=self.user.region.id)
                self.fields['district'].queryset = Districts.objects.filter(region=self.user.region)
                self.fields['depot'].queryset = Depots.objects.filter(region=self.user.region)

CellFormSet = inlineformset_factory(
    BatteryInstallation,
    Cell,
    form=CellForm,
    fields=['specific_gravity', 'voltage'],
    extra=5,
    can_delete=False
)
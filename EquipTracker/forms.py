from django import forms
from .models import TrackEquipment, EquipmentChange
from it.users.models import Sections, Substation
from django.forms import ModelForm, DateInput

FIELD_CSS_CLASSES = "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
class TrackEquipmentForm(ModelForm):
    class Meta:
        model = TrackEquipment
        fields = ['type_of_equipment']
        widgets = {
            'type_of_equipment': forms.Select(attrs={'class': 'form-control'}),
        }
        
class EquipmentChangeForm(ModelForm):
    class Meta:
        model = EquipmentChange
        fields = "__all__"
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': FIELD_CSS_CLASSES})
            classes = FIELD_CSS_CLASSES
            if field_name in ['substation']:
                classes += ' select2' 
            field.widget.attrs.update({'class': classes})
            
        if user and hasattr(user, 'region'):
            self.fields['substation'].queryset = Substation.objects.filter(region=user.region)

 

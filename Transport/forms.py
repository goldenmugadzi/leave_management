from django import forms
from .models import TripRecord
from datetime import datetime

class  TripRecordForm(forms.ModelForm):
    class Meta:
        model = TripRecord
        fields = '__all__'
        exclude = ['year','total_km','total_oil','total_fuel','average_consumption','trp_distance','designation']
        
        widgets = {
             'date': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'form-control'}
            ),
           
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset "
                         "ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 "
                         "sm:text-sm sm:leading-6",
            })

            if field_name in ['cost_center', 'vehicle_details','drivers_name', 'designation', 'department', 'region', 'status','place_drawn', 'fuel_type','depot']:
                field.widget.attrs.update({
                    'class': "select2 block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset "
                             "ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 "
                             "sm:text-sm sm:leading-6",
                })

            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'rows': '3'})
                
from django import forms
from .models import TripRecord


class TripDetailsForm(forms.ModelForm):
    class Meta:
        model =  TripRecord
        fields = [
            "vehicle_details",
            "drivers_name",
            "date",
            "stf_number",
            "opening_speedo_reading",
            "closing_speedo_reading",
            "details_of_journey",
           
        ]
        widgets = {
            "vehicle_details": forms.Select(attrs={
                "class": "w-full rounded-md border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500 text-sm"
            }),
            "drivers_name": forms.Select(attrs={
                "class": "w-full rounded-md border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500 text-sm"
            }),
            "date": forms.DateInput(attrs={
                "type": "date",
                "class": "w-full rounded-md border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500 text-sm"
            }),
            "stf_number": forms.TextInput(attrs={
                "class": "w-full rounded-md border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500 text-sm"
            }),
            "opening_speedo_reading": forms.NumberInput(attrs={
                "class": "w-full rounded-md border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500 text-sm"
            }),
            "closing_speedo_reading": forms.NumberInput(attrs={
                "class": "w-full rounded-md border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500 text-sm"
            }),
            "details_of_journey": forms.Textarea(attrs={
                "rows": 3,
                "class": "w-full rounded-md border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500 text-sm"
            }),
        }


from django import forms
from .models import TripRecord, Tyres, Battery, Allocation
from datetime import datetime

class TripRecordForm(forms.ModelForm):
    class Meta:
        model = TripRecord
        fields = '__all__'
        exclude = ['year', 'total_km', 'total_oil', 'total_fuel', 'average_consumption','stf_number']

        widgets = {
            'date': forms.DateTimeInput(
                attrs={'type': 'datetime-local'}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            # base style for all inputs
            field.widget.attrs.update({
                'class': (
                    "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm "
                    "ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 "
                    "focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                ),
            })

            # Select2-enhanced fields
            if field_name in [
                'cost_center', 'vehicle_details', 'drivers_name', 'department',
                'region', 'depot', 'place_drawn'
            ]:
                field.widget.attrs.update({'class': field.widget.attrs['class'] + " select2"})

            # Textareas
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'rows': '3'})

        # Mark optional fields (remove required from model level if needed)
        for optional in ['fuel_drawn', 'oil_drawn', 'place_drawn']:
            if optional in self.fields:
                self.fields[optional].required = False

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

class TyresForm(forms.ModelForm):
    class Meta:
        model = Tyres
        fields = ['name', 'quantity', 'size', 'date_fitted']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.TextInput(attrs={'class': 'form-control'}),
            'size': forms.NumberInput(attrs={'class': 'form-control'}),
            'date_fitted': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class BatteryForm(forms.ModelForm):
    class Meta:
        model = Battery
        fields = ['name', 'number', 'date_fitted']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'number': forms.NumberInput(attrs={'class': 'form-control'}),
            'date_fitted': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class AllocationForm(forms.ModelForm):
    class Meta:
        model = Allocation
        fields = ['kms', 'job_number', 'amount']
        widgets = {
            'kms': forms.TextInput(attrs={'class': 'form-control'}),
            'job_number': forms.NumberInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
        }


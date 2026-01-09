from django import forms
from .models import TripRecord, Tyres, Battery, Allocation, Vehicle, TransportAssets
from datetime import datetime

class TripRecordForm(forms.ModelForm):
    vehicle_details = forms.ModelChoiceField(
        queryset=Vehicle.objects.all(),
        widget=forms.Select,
        label="Fleet/Make/Reg Number",
        to_field_name="id"
    )
    class Meta:
        model = TripRecord
        fields = '__all__'
        exclude = ['year', 'total_km', 'total_oil', 'total_fuel', 'average_consumption', 'stf_number', 'trip_reference']
        widgets = {
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ✅ Apply consistent styling to all form fields
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': (
                    "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm "
                    "ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 "
                    "focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                ),
            })

            # Apply select2 to dropdowns
            if field_name in [
                'cost_center', 'vehicle_details', 'drivers_name',
                'department', 'region', 'depot', 'place_drawn'
            ]:
                field.widget.attrs.update({'class': field.widget.attrs['class'] + " select2"})

            # Make textareas taller
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'rows': '3'})

        # ✅ Optional fields
        for optional in ['fuel_drawn', 'oil_drawn', 'place_drawn', 'closing_speedo_reading', 'trip_distance']:
            if optional in self.fields:
                self.fields[optional].required = False

        # ✅ Populate opening_speedo_reading automatically
        vehicle_id = None

        # 1️⃣ Check for bound POST data first
        if self.is_bound:
            vehicle_id = self.data.get('vehicle_details') or self.initial.get('vehicle_details')
        # 2️⃣ Check instance or initial data for unbound form
        elif hasattr(self, 'instance') and getattr(self.instance, 'vehicle_details', None):
            vehicle_id = getattr(self.instance.vehicle_details, 'id', None)
        elif self.initial.get('vehicle_details'):
            vehicle_id = self.initial.get('vehicle_details')

        # 3️⃣ Auto-set initial opening_speedo_reading if a vehicle is selected
        if vehicle_id and not self.is_bound:
            try:
                last_trip = TripRecord.objects.filter(vehicle_details_id=vehicle_id).order_by('-date').first()
                if last_trip:
                    self.fields['opening_speedo_reading'].initial = last_trip.closing_speedo_reading
                else:
                    # fallback to TransportAssets
                    from .models import Vehicle, TransportAssets
                    vehicle_obj = Vehicle.objects.filter(pk=vehicle_id).first()
                    if vehicle_obj:
                        ta = TransportAssets.objects.filter(reg_number=vehicle_obj.reg_number).order_by('-id').first()
                        if ta and ta.closing_speedo_reading is not None:
                            self.fields['opening_speedo_reading'].initial = ta.closing_speedo_reading
            except Exception as e:
                print("Speedometer preload error:", e)


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

class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = ['reg_number', 'fleet_number', 'make', 'model', 'year', 'fuel_drawn', 'oil_drawn', 'fuel_type']
        widgets = {
            'year': forms.TextInput(attrs={'type': 'number', 'class': 'form-control'}),
            'fuel_type': forms.Select(attrs={'class': 'form-control'}),
        }


from django import forms
from .models import SafetyMonthlyReport, AccidentReport, VehicleAccidentReport, PropertyLossIncident
from it.users.models import UserProfile, Sections, Regions

class SafetyMonthlyReportForm(forms.ModelForm):
    class Meta:
        model = SafetyMonthlyReport
        fields = [
            'user', 'department', 'regions', 'date', 'month', 'year',
            'work_related_accidents', 'disabling_accidents', 'fatal_accidents',
            'man_hours_lost', 'accident_free_days', 'motor_vehicle_accidents',
            'property_damaged', 'she_meetings_conducted', 'she_related_trainings',
            'wellness_programmes', 'clear_up_campaigns', 'she_inspections_conducted',
            'mock_drills_conducted', 'number_of_workers', 'number_of_days'
        ]
        
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field, forms.ModelChoiceField):
                field.widget.attrs.update({'class': 'select2 form-control'})

class  AccidentReportForm(forms.ModelForm):
    class Meta:
        model =  AccidentReport
        fields = '__all__'
        
        
        widgets = {
            'date_of_accident': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'time_of_accident': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
             'authority_received_datetime': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'form-control'}
            ),
            'authority_received_from': forms.TextInput(
                attrs={'class': 'form-control'}
            ),
            'police_received_datetime': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'form-control'}
            ),
            'police_received_from': forms.TextInput(
                attrs={'class': 'form-control'}
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

            if (field_name == 'employee_involved') or (field_name == 'sex') or ( field_name == 'cost_center') or ( field_name == 'department') or ( field_name == 'severity_Of_Accident ') or  (field_name == 'nature_of_injury') or (field_name == 'region') or (field_name == 'nature_of_accident') or (field_name == 'risk_assessment_carried_out') or (field_name == 'safety_preparation_carried_out') or (field_name == 'for_electrical_state_voltage'):
                field.widget.attrs.update({'class': "select2 block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",})
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'rows': '3'})


class VehicleAccidentReportForm(forms.ModelForm):
    class Meta:
        model = VehicleAccidentReport
        fields = '__all__'

        widgets = {
            'date_of_issue': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'datetime_for_accident': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'datetime_to_police': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'datetime_for_accident':forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset "
                         "ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 "
                         "sm:text-sm sm:leading-6",
            })

            # Apply Select2 class to relevant dropdown-like fields (if applicable)
            if field_name in [
                'designation', 'allocation_to_section', 'work_station',
            ]:
                field.widget.attrs.update({
                    'class': "select2 block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 "
                             "ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset "
                             "focus:ring-indigo-600 sm:text-sm sm:leading-6",
                })

            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'rows': '3'})


class PropertyLossIncidentForm(forms.ModelForm):
    class Meta:
        model = PropertyLossIncident
        fields = '__all__'
        widgets = {
            'date_time_of_loss': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'zetdc_report_received_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'zrp_report_received_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'date_of_report': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

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
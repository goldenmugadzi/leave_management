from django import forms
from it.users.models import UserProfile, Sections, Regions,Designations

class SafetyMonthlyReportForm(forms.ModelForm):
    class Meta:
        from .models import SafetyMonthlyReport
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


class AccidentReportForm(forms.ModelForm):
    class Meta:
        from .models import AccidentReport
        model = AccidentReport
        fields = '__all__'
        widgets = {
            'date_of_accident': forms.DateInput(attrs={'type': 'date'}),
            'time_of_accident': forms.TimeInput(attrs={'type': 'time'}),
            'authority_received_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'police_received_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset "
                            "ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 "
                            "sm:text-sm sm:leading-6",
            })

            if (field_name == 'employee_involved') or (field_name == 'gender') or ( field_name == 'cost_center') or ( field_name == 'department') or ( field_name == 'severity_Of_Accident ') or  (field_name == 'nature_of_injury') or (field_name == 'region') or (field_name == 'nature_of_accident') or (field_name == 'risk_assessment_carried_out') or (field_name == 'safety_preparation_carried_out') or (field_name == 'for_electrical_state_voltage'):
                field.widget.attrs.update({'class': "select2 block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",})
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'rows': '3'})


class VehicleAccidentReportForm(forms.ModelForm):
    class Meta:
        from .models import VehicleAccidentReport
        model = VehicleAccidentReport
        fields = '__all__'
        widgets = {
            'date_of_issue': forms.DateInput(attrs={'type': 'date'}),
            'datetime_for_accident': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'datetime_to_police': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset "
                         "ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 "
                         "sm:text-sm sm:leading-6",
            })

            if (field_name == 'designation') or (field_name == 'driver_name') or ( field_name == 'state_if_hired') or ( field_name == 'department') or ( field_name == 'vehicle_details'):
                    field.widget.attrs.update({'class': "select2 block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",})
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'rows': '3'})



class PropertyLossIncidentForm(forms.ModelForm):
    class Meta:
        from .models import PropertyLossIncident
        model = PropertyLossIncident
        fields = '__all__'
        widgets = {
            'date_time_of_loss': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'zetdc_report_received_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'zrp_report_received_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'date_of_report': forms.DateInput(attrs={'type': 'date'}),
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
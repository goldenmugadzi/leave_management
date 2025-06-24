from django import forms
<<<<<<< HEAD
from .models import SafetyMonthlyReport, AccidentReport
=======
from .models import SafetyMonthlyReport
>>>>>>> 1b24c077b0267638fdc753da98de11aedc9afed6
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
<<<<<<< HEAD
        
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
=======
>>>>>>> 1b24c077b0267638fdc753da98de11aedc9afed6

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
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset "
                            "ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 "
                            "sm:text-sm sm:leading-6",
            })

            if (field_name == 'employee_involved') or ( field_name == 'cost_center') or ( field_name == 'department') or ( field_name == 'type_of_accident') or  (field_name == 'nature_of_injury') or (field_name == 'regions') or (field_name == 'nature_of_accident'):
                field.widget.attrs.update({'class': "select2 block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",})
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'rows': '3'})

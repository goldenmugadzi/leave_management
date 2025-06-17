from django import forms
from .models import SafetyMonthlyReport
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
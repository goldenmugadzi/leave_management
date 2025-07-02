from django import forms
from .models import LeaveRequest, LeaveTypes

class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = [
            'ecnumber', 'type_of_leave',  'position', 'gender',
            'start_date', 'end_date', 'department',
            'region',
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset "
                         "ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 "
                         "sm:text-sm sm:leading-6",
            })

            if (field_name == 'user') or ( field_name == 'type_of_leave') or ( field_name == 'department') or ( field_name == 'region') or ( field_name == 'gender') or ( field_name == 'position'):
                field.widget.attrs.update({'class': "select2 block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",})
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'rows': '3'})

class LeaveTypesForm(forms.ModelForm):
    class Meta:
        model = LeaveTypes
        fields = [
            'leave_for_national_events',
            'sick_leave',
            'maternity_leave',
            'special_leave',
            'unpaid_leave',
            'vacation_leave',
            'study_leave',
            'occasional_leave',
            'mandatory_leave',
        ]


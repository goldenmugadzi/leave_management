from django import forms
from .models import LeaveRequest,LeaveTypes

class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        exclude = ['days_taken', 'days_encashed', 'total_days', 'gender']
        fields = [
            'employee_types', 'type_of_leave', 
            'start_date', 'attachments', 'end_date',
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'attachments': forms.ClearableFileInput(attrs={
                'class': 'block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Force these fields to be required for normal leave requests
        self.fields['start_date'].required = True
        self.fields['end_date'].required = True

        base_class = (
            "block w-full rounded-md border-0 py-2 px-3 text-gray-900 "
            "shadow-sm ring-1 ring-inset ring-gray-300 "
            "placeholder:text-gray-400 focus:ring-2 focus:ring-inset "
            "focus:ring-indigo-600 sm:text-sm sm:leading-6"
        )

        select2_fields = ['user', 'employee_types', 'type_of_leave', 'department', 'region', 'gender', 'position']

        for field_name, field in self.fields.items():
            current_class = field.widget.attrs.get('class', '')
            classes = base_class
            if field_name in select2_fields:
                classes += " select2"
            field.widget.attrs['class'] = f"{current_class} {classes}".strip()

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
            'user',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        base_class = (
            "block w-full rounded-md border-0 py-2 px-3 text-gray-900 "
            "shadow-sm ring-1 ring-inset ring-gray-300 "
            "placeholder:text-gray-400 focus:ring-2 focus:ring-inset "
            "focus:ring-indigo-600 sm:text-sm sm:leading-6"
        )
        select2_fields = ['user']
        for field_name, field in self.fields.items():
            current_class = field.widget.attrs.get('class', '')
            classes = base_class
            if field_name in select2_fields:
                classes += " select2"
            field.widget.attrs['class'] = f"{current_class} {classes}".strip()



class LeaveRequestFullForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = [
            'type_of_leave',
            'start_date',
            'end_date',
            'days_taken',
            'days_encashed',
            'total_days',
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Make certain fields optional
        optional_fields = ['start_date', 'end_date', 'days_taken']
        for field_name in optional_fields:
            self.fields[field_name].required = False

        # Apply shared styling
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': (
                    "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset "
                    "ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 "
                    "sm:text-sm sm:leading-6"
                ),
            })
            if field_name == 'type_of_leave':
                field.widget.attrs.update({
                    'class': (
                        "select2 block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 "
                        "ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset "
                        "focus:ring-indigo-600 sm:text-sm sm:leading-6"
                    ),
                })
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'rows': '3'})



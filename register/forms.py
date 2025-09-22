from django import forms
from .models import AttendanceRecord

class AttendanceRecordForm(forms.ModelForm):
    class Meta:
        model = AttendanceRecord
        fields = ['department', 'user', 'status', 'reason', 'date']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'status': forms.RadioSelect(),  # <-- use radio buttons here
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            if field_name == 'status':
                # You may want custom classes here if needed
                continue
            
            field.widget.attrs.update({
                'class': (
                    "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm "
                    "ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 "
                    "focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                )
            })

            if field_name in ['user', 'department', 'reason']:
                field.widget.attrs.update({
                    'class': (
                        "select2 block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm "
                        "ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 "
                        "focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                    )
                })

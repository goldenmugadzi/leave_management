from django import forms
from .models import *

class  MeetingsForm(forms.ModelForm):
    class Meta:
        model =  Meetings
        fields = '__all__'
        exclude = ['comments','confirm_status']
        
        
        widgets = {
            'date_of_meeting': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset "
                         "ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 "
                         "sm:text-sm sm:leading-6",
            })

            if (field_name == 'employees_invited') or (field_name == 'confirm_status')or ( field_name == 'cost_center') or ( field_name == 'department') or ( field_name == 'type_of_meeting') or ( field_name == 'regions') or (field_name == 'depot') or (field_name == 'venue') :
                field.widget.attrs.update({'class': "select2 block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",})
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'rows': '3'})

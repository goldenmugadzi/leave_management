from django import forms
from .models import Meetings, VenueBooking, Venue, Sections

class MeetingsForm(forms.ModelForm):
    class Meta:
        model = Meetings
        fields = '__all__'
        exclude = ['comments', 'confirm_status', 'list_of_invited_attendees']  # excluded on create
        widgets = {
            'date_of_meeting': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            css_class = "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 " \
                        "ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset " \
                        "focus:ring-indigo-600 sm:text-sm sm:leading-6"
            if isinstance(field, forms.ModelChoiceField):
                field.widget.attrs.update({'class': css_class + ' select2'})
            else:
                field.widget.attrs.update({'class': css_class})

class MeetingsUpdateForm(forms.ModelForm):
    class Meta:
        model = Meetings
        fields = '__all__'
        exclude = ['regions', 'depot', 'cost_center', 'employees_invited']
        widgets = {
            'date_of_meeting': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 "
                         "ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset "
                         "focus:ring-indigo-600 sm:text-sm sm:leading-6",
            })


class VenueBookingForm(forms.ModelForm):
    class Meta:
        model = VenueBooking
        fields = ['venue', 'department', 'start_time', 'end_time', 'date_of_meeting', 'type_of_meeting', 'capacity']
        widgets = {
            'date_of_meeting': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'type_of_meeting': forms.Select(attrs={'class': 'select2 form-control'}),  # ✅ force select dropdown
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['capacity'].widget.attrs['readonly'] = True
        self.fields['venue'].label_from_instance = lambda obj: f"{obj.name}  - Capacity: {obj.capacity}"

        # Keep select2 for dropdowns
        for field_name, field in self.fields.items():
            if isinstance(field, forms.ModelChoiceField):
                field.widget.attrs.update({'class': 'select2 form-control'})
            elif field_name != 'type_of_meeting':  # skip because we forced widget above
                field.widget.attrs.update({'class': 'form-control'})


from django import forms
from .models import Meetings, VenueBooking, Venue, Sections

class MeetingsForm(forms.ModelForm):
    class Meta:
        model = Meetings
        fields = '__all__'
        exclude = ['comments', 'confirm_status', 'list_of_invited_attendees', 'regions', 'depot','actual_cost_of_meeting']  # excluded on create
        widgets = {
            'start_date':forms.DateInput(attrs={'type':'date', 'class': 'form-control'}),
            'end_date':forms.DateInput(attrs={'type':'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        initial = kwargs.get('initial', {})
        instance = kwargs.get('instance', None)
        super().__init__(*args, **kwargs)
        # Custom label for booking dropdown
        for field_name, field in self.fields.items():
            css_class = "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 " \
                        "ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset " \
                        "focus:ring-indigo-600 sm:text-sm sm:leading-6"
            if field_name == 'booking' and hasattr(field, 'label_from_instance'):
                field.label_from_instance = lambda obj: f"{obj.venue}" if obj.venue else str(obj)
                # Ensure booking dropdown is styled and searchable like other select2 dropdowns
                field.widget.attrs.update({'class': css_class + ' select2'})
            elif isinstance(field, forms.ModelChoiceField):
                field.widget.attrs.update({'class': css_class + ' select2'})
            else:
                field.widget.attrs.update({'class': css_class})

        # Auto-populate fields from selected booking
        booking_obj = None
        booking_id = None
        # Check if booking is in initial or instance
        if 'booking' in initial and initial['booking']:
            booking_id = initial['booking'] if isinstance(initial['booking'], int) else getattr(initial['booking'], 'id', None)
        elif instance and getattr(instance, 'booking_id', None):
            booking_id = instance.booking_id
        if booking_id:
            try:
                from meetings.models import VenueBooking
                booking_obj = VenueBooking.objects.get(pk=booking_id)
            except Exception:
                booking_obj = None
        if booking_obj:
            # Set initial values for fields from booking
            self.fields['venue'].initial = booking_obj.venue
            self.fields['start_date'].initial = booking_obj.start_date
            self.fields['end_date'].initial = booking_obj.end_date
            if 'start_time' in self.fields:
                self.fields['start_time'].initial = booking_obj.start_time
            if 'end_time' in self.fields:
                self.fields['end_time'].initial = booking_obj.end_time

class MeetingsUpdateForm(forms.ModelForm):
    class Meta:
        model = Meetings
        fields = '__all__'
        exclude = ['regions', 'depot', 'cost_center', 'employees_invited', 'list_of_invited_attendees','booking']
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
        fields = '__all__'
        exclude = ['created_by']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'type_of_meeting': forms.Select(attrs={'class': 'select2 form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['capacity'].widget.attrs['readonly'] = True
        self.fields['venue'].label_from_instance = lambda obj: f"{obj.name}  - Capacity: {obj.capacity}"
        for field_name, field in self.fields.items():
            if isinstance(field, forms.ModelChoiceField):
                field.widget.attrs.update({'class': 'select2 form-control'})
            elif field_name != 'type_of_meeting': 
                field.widget.attrs.update({'class': 'form-control'})
        # Set default status if not provided
   


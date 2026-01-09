from django import forms
from .models import OvertimeEntry

class OvertimeEntryForm(forms.ModelForm):
    class Meta:
        model = OvertimeEntry
        fields = [
            "month",
            "period_from",
            "period_to",
            "district_station",
            "designation",
            "ec_number",
            "created_at",
            "created_by",
            "nature_of_work",
            "time_out",
            "time_in",
            "hours",
            "job_vote_number",
        ]
        widgets = {
            'period_from': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'period_to': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'created_at': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'time_out': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'time_in': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Auto-populate and lock designation and ec_number from user
        if user is not None and hasattr(user, 'userprofile'):
            self.fields['designation'].initial = user.userprofile.designation
            self.fields['ec_number'].initial = user.userprofile.ec_number
            self.fields['designation'].disabled = True
            self.fields['ec_number'].widget.attrs['readonly'] = True

        # Make certain fields required
        self.fields['period_from'].required = True
        self.fields['period_to'].required = True
        self.fields['time_out'].required = True
        self.fields['time_in'].required = True

        base_class = (
            "block w-full rounded-md border-0 py-2 px-3 text-gray-900 "
            "shadow-sm ring-1 ring-inset ring-gray-300 "
            "placeholder:text-gray-400 focus:ring-2 focus:ring-inset "
            "focus:ring-indigo-600 sm:text-sm sm:leading-6"
        )

        select2_fields = ['designation', 'created_by']

        for field_name, field in self.fields.items():
            current_class = field.widget.attrs.get('class', '')
            classes = base_class
            if field_name in select2_fields:
                classes += " select2"
            field.widget.attrs['class'] = f"{current_class} {classes}".strip()
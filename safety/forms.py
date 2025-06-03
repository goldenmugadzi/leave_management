from django import forms
from .models import SafetyMonthlyReport
from it.users.models import UserProfile, Sections,Regions

class SafetyMonthlyReportForm(forms.Form):
    
    # User and department
    user = forms.ModelChoiceField(queryset=UserProfile.objects.all(), required=False)
    department = forms.ModelChoiceField(queryset=Sections.objects.all(), required=False)
    regions = forms.ModelChoiceField(queryset=Regions.objects.all(), required=False)

    # Date fields
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    month = forms.IntegerField(min_value=1, max_value=12)
    year = forms.IntegerField(min_value=1900)

    # Accident statistics
    work_related_accidents = forms.IntegerField(min_value=0, required=True)
    disabling_accidents = forms.IntegerField(min_value=0, required=True)
    fatal_accidents = forms.IntegerField(min_value=0, required=True)
    man_hours_lost = forms.IntegerField(min_value=0, required=True, label="Man hours lost due to injury")
    accident_free_days = forms.IntegerField(min_value=0, required=True)
    motor_vehicle_accidents = forms.IntegerField(min_value=0, required=True)
    property_damaged = forms.IntegerField(min_value=0, required=True)
    she_meetings_conducted = forms.IntegerField(min_value=0, required=True)
    she_related_trainings = forms.IntegerField(min_value=0, required=True)
    wellness_programmes = forms.IntegerField(min_value=0, required=True)
    clear_up_campaigns = forms.IntegerField(min_value=0, required=True)
    she_inspections_conducted = forms.IntegerField(min_value=0, required=True)
    mock_drills_conducted = forms.IntegerField(min_value=0, required=True)
    
    
    

    # Exposure
    number_of_workers = forms.IntegerField(min_value=0, required=True)
    number_of_days = forms.IntegerField(min_value=0, required=True)

    # Calculated rates (optional, can be left blank)
    accident_frequency_rate = forms.FloatField(required=False, disabled=False)
    injury_severity_rate = forms.FloatField(required=False, disabled=False)

    # Year-to-date cumulative fields (optional)
    ytd_work_related_accidents = forms.IntegerField(min_value=0, required=False)
    ytd_disabling_accidents = forms.IntegerField(min_value=0, required=False)
    ytd_fatal_accidents = forms.IntegerField(min_value=0, required=False)
    ytd_man_hours_lost = forms.IntegerField(min_value=0, required=False)
    ytd_motor_vehicle_accidents = forms.IntegerField(min_value=0, required=False)
    ytd_property_damaged = forms.IntegerField(min_value=0, required=False)

    def save(self, commit=True):
        cleaned = self.cleaned_data
        # Calculate rates
        exposure_time = cleaned['number_of_days'] * 7.5 * cleaned['number_of_workers']
        if exposure_time > 0:
            afr = (cleaned['work_related_accidents'] / exposure_time) * 1_000_000
            isr = (cleaned['man_hours_lost'] / exposure_time) * 1_000_000
        else:
            afr = 0
            isr = 0

        report = SafetyMonthlyReport(
            user=cleaned.get('user'),
            department=cleaned.get('department'),
            date=cleaned['date'],
            month=cleaned['month'],
            year=cleaned['year'],
            work_related_accidents=cleaned['work_related_accidents'],
            disabling_accidents=cleaned['disabling_accidents'],
            fatal_accidents=cleaned['fatal_accidents'],
            man_hours_lost=cleaned['man_hours_lost'],
            accident_free_days=cleaned['accident_free_days'],
            motor_vehicle_accidents=cleaned['motor_vehicle_accidents'],
            property_damaged=cleaned['property_damaged'],
            number_of_workers=cleaned['number_of_workers'],
            number_of_days=cleaned['number_of_days'],
            accident_frequency_rate=afr,
            injury_severity_rate=isr,
            ytd_work_related_accidents=cleaned.get('ytd_work_related_accidents') or 0,
            ytd_disabling_accidents=cleaned.get('ytd_disabling_accidents') or 0,
            ytd_fatal_accidents=cleaned.get('ytd_fatal_accidents') or 0,
            ytd_man_hours_lost=cleaned.get('ytd_man_hours_lost') or 0,
            ytd_motor_vehicle_accidents=cleaned.get('ytd_motor_vehicle_accidents') or 0,
            ytd_property_damaged=cleaned.get('ytd_property_damaged') or 0,
        )
        if commit:
            report.save()
        return report

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field, forms.ModelChoiceField):
                field.widget.attrs.update({'class': 'select2 form-control'})
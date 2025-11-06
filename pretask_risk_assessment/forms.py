from django import forms
from .models import PretaskRiskAssessment, Job

FIELD_CSS_CLASSES = "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"

class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = "__all__"
        exclude = ['issuing_senior_authorised_person']
    def __init__(self, *args, user=None, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and hasattr(user, 'region'):
            self.fields['substation'].queryset = Substation.objects.filter(region=user.region)
            self.fields['competent_person'].queryset = UserProfile.objects.filter(region_id=str(user.region.id))
            self.fields['issuing_senior_authorised_person'].queryset = UserProfile.objects.filter(region_id=str(user.region.id))

        for field_name, field in self.fields.items():
            classes = FIELD_CSS_CLASSES
            if field_name in ['substation', 'competent_person']:
                classes += ' select2'
            field.widget.attrs.update({'class': classes})
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'rows': '3'})
class PretaskRiskAssessmentForm(forms.ModelForm):
    class Meta:
        model = PretaskRiskAssessment
        fields = ['job', 'equipment', 'harzard', 'control_measures']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            classes = FIELD_CSS_CLASSES
            if field_name in ['job', 'equipment']:
                classes += ' select2'
            field.widget.attrs.update({'class': classes})
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'rows': '3'})
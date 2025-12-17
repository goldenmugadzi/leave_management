from django import forms
from .models import PretaskRiskAssessment, Job


class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = "__all__"
        exclude = ['issuing_senior_authorised_person']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({ 'class': "block w-full rounded-md border-0 my-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",})
            if isinstance(field.widget, forms.Textarea): field.widget.attrs.update({'rows': '3'})
            if (field_name == 'substation') or (field_name == 'competent_person') :
                field.widget.attrs.update({
                    'class': "select2 0 block w-full rounded-md border-0 py-1.5 text-gray-900 "
                             "shadow-sm ring-1 ring-inset ring-gray-300 "
                             "placeholder:text-gray-400 focus:ring-2 focus:ring-inset "
                             "focus:ring-indigo-600 sm:text-sm sm:leading-6", })
           
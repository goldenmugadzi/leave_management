from django import forms
from .models import TransportAssets
from datetime import datetime

class TransportAssetsForm(forms.ModelForm):
    class Meta:
        model = TransportAssets
        fields = '__all__'
        exclude = ['jobcardnumber','updated_by']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Generate a list of years from current year to 10 years ago
        current_year = datetime.now().year
        year_choices = [(str(year), str(year)) for year in range(current_year, current_year - 10, -1)]

        # Assign the year choices to the 'year' field
        self.fields['year'].widget = forms.Select(choices=year_choices)

        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset "
                         "ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 "
                         "sm:text-sm sm:leading-6",
            })

            if field_name in ['cost_center', 'user', 'designation', 'department', 'created_by', 'regions', 'status', 'fuel_type','year']:
                field.widget.attrs.update({
                    'class': "select2 block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset "
                             "ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 "
                             "sm:text-sm sm:leading-6",
                })

            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'rows': '3'})

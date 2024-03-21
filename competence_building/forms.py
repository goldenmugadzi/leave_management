from django import forms
from .models import Document

class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = "__all__" #['category', 'name', 'region', 'section', 'file', 'created_by']
        exclude=['created_by']
   
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",
            })

            # field.label = field.label or field_name.replace('_', ' ').capitalize()
            # field.label_attrs = {'class': 'block text-sm font-medium leading-6 text-gray-900'}
          
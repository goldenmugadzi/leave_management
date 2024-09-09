# users/forms.py

from django.contrib.auth.forms import UserCreationForm
from django import forms
from .models import Responsibilities

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        fields = UserCreationForm.Meta.fields + ("email",)
    
    def __init__(self, *args, **kwargs):
        super(UserCreationForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['email'].widget.attrs.update({'class': 'form-control'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})

class ResponsibilitiesForm(forms.ModelForm):
    class Meta:
        model = Responsibilities
        fields = "__all__"
        exclude = ['user']
        # widgets = {
        #     'role': forms.Select(attrs={'class': 'form-control select2'}),
        #     'cost_centers': forms.Select(attrs={'class': 'form-control select2','multiple': 'multiple'}),
        # }
    def __init__(self, *args, **kwargs):
        roles_queryset = kwargs.pop('roles_queryset', None)
        cost_centers_queryset = kwargs.pop('cost_centers_queryset', None)
        super().__init__(*args, **kwargs)

        if roles_queryset is not None:
            self.fields['role'].queryset = roles_queryset
        if cost_centers_queryset is not None:
            self.fields['cost_centers'].queryset = cost_centers_queryset

        for field_name, field in self.fields.items():
            if(field_name == 'cost_centers'):
                field.widget.attrs.update({
                 'multiple': 'multiple',   'class': "block w-full hidden rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",
                })
            else:
                field.widget.attrs.update({
                'class': "imline m-3   px-2 form-control select2 text-center rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",
            })
   
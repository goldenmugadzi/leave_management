from django import forms
from django.contrib.auth.models import User
from .models import *
from django.forms import formset_factory


class QuotationForm(forms.ModelForm):
    class Meta:
        model = Quotation
        fields = ['quotation_file']


QuotationFormSet = formset_factory(QuotationForm, extra=0, min_num=1, validate_min=True)


class AceForm(forms.ModelForm):
    class Meta:
        model = Ace2
        fields = '__all__'
        exclude = ['process', 'allocation_code_of_expenditure', 'requested_by', 'date_created'
            , 'Ace_id2', 'Ace_id', 'asset_number', 'designation', 'region'
                   # exclude the project items
            , 'capital_estimated', 'capital_sanctioned', 'capital_contribution', 'materials', 'labour',
                   'connection_fee', 'transport', 'present_tariff', 'present_fmc', 'total_connection_fee'
                   ]

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

            for field_name, field in self.fields.items():
                # for the field budget i want it to display its balance attribute when it selected

                field.widget.attrs.update({
                    'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset "
                             "ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset "
                             "focus:ring-indigo-600"
                             "sm:text-sm sm:leading-6",
                })
                if isinstance(field.widget, forms.Textarea):
                    field.widget.attrs.update({'rows': '3'})

                field.label = field.label or self.humanize_field_name(field_name)
                field.label_attrs = {'class': 'block text-sm font-medium leading-6 text-gray-900'}

            self.formset = QuotationForm(*args, **kwargs)

            for i, quotation_form in enumerate(self.formset.forms):
                quotation_form.fields['quotation_file'].widget.attrs.update({
                    'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 bg-white shadow-sm ring-1 "
                             "ring-inset"
                             "ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset "
                             "focus:ring-indigo-600"
                             "sm:text-sm sm:leading-6",
                })
                quotation_form.fields['quotation_file'].label = self.get_quotation_label(i + 1)

            # if field is budget display the balnce and name

    def humanize_field_name(self, field_name):
        words = field_name.split('_')
        capitalized_words = [word.capitalize() for word in words]
        return ' '.join(capitalized_words)

    def get_quotation_label(self, quotation_number):
        suffix = 'ACE' if 11 <= quotation_number <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(quotation_number % 10, 'th')
        return f"{quotation_number}{suffix} Quotation"

    def clean(self):
        cleaned_data = super().clean()
        quotation_files = set()

        for quotation_form in cleaned_data.get('quotations', []):
            quotation_file = quotation_form.cleaned_data.get('quotation_file')
            if quotation_file in quotation_files:
                raise forms.ValidationError('Each quotation file must be distinct.')
            quotation_files.add(quotation_file)

        return cleaned_data


class ProjectDetailForm(forms.ModelForm):
    class Meta:
        model = Ace2
        fields = '__all__'
        exclude = ['process', 'allocation_code_of_expenditure', 'requested_by', 'date_created', 'Ace_id', 'asset_number'
            , 'designation', 'region', 'amount', 'budget_id', 'currency', 'classification', 'Ace_id2',
                   'details_of_expenditure', 'quantity', 'total_connection_fee'
                   # include the project items
                   ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            # for the field budget, I want it to display its balance attribute when it selected

            field.widget.attrs.update({
                'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset "
                         "ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset "
                         "focus:ring-indigo-600"
                         "sm:text-sm sm:leading-6",
            })
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'rows': '3'})

            field.label = field.label or self.humanize_field_name(field_name)
            field.label_attrs = {'class': 'block text-sm font-medium leading-6 text-gray-900'}

        # self.formset = QuotationForm(*args, **kwargs)
        #
        # for i, quotation_form in enumerate(self.formset.forms):
        #     quotation_form.fields['quotation_file'].widget.attrs.update({
        #         'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 bg-white shadow-sm ring-1 "
        #                  "ring-inset"
        #                  "ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset "
        #                  "focus:ring-indigo-600"
        #                  "sm:text-sm sm:leading-6",
        #     })
        # quotation_form.fields['quotation_file'].label = self.get_quotation_label(i + 1)

    # def get_quotation_label(self, quotation_number): suffix = 'ACE' if 11 <= quotation_number <= 13 else {1: 'st',
    # 2: 'nd', 3: 'rd'}.get(quotation_number % 10, 'th') return f"{quotation_number}{suffix} Quotation"

    def clean(self):
        cleaned_data = super().clean()
        quotation_files = set()

        for quotation_form in cleaned_data.get('quotations', []):
            quotation_file = quotation_form.cleaned_data.get('quotation_file')
            if quotation_file in quotation_files:
                raise forms.ValidationError('Each quotation file must be distinct.')
            quotation_files.add(quotation_file)

        return cleaned_data

    def humanize_field_name(self, field_name):
        words = field_name.split('_')
        capitalized_words = [word.capitalize() for word in words]
        return ' '.join(capitalized_words)

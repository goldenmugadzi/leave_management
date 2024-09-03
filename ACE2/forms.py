from django import forms
from django.contrib.auth.models import User
from .models import *
from django.forms import formset_factory
from it.users.models import UserProfile, Regions, Sections, Designations


class QuotationForm(forms.ModelForm):
    class Meta:
        model = Quotation
        fields = ['quotation_file']


QuotationFormSet = formset_factory(QuotationForm, extra=0, min_num=1, validate_min=True)


class AceForm(forms.ModelForm):
    print("AceForm1")

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

        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        print("user", user)

        if user:
            user_profile = UserProfile.objects.filter(username=user.username).first()
            if user_profile:
                region = user_profile.region
                region_id = Regions.objects.filter(region=region).first()

                print("region", region)
                self.fields['budget_id'].queryset = AssetBudget.objects.filter(period=2024, region=region)
                self.fields['section'].queryset = Sections.objects.filter(region_id=region_id.id)

        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset "
                         "ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 "
                         "sm:text-sm sm:leading-6",
            })
            # self.fields['budget_id'].queryset = AssetBudget.objects.filter(period=2024)

            if (field_name == 'budget_id') or (field_name == 'section'):
                field.widget.attrs.update({
                    'class': "select2 block w-full rounded-md border-0 py-1.5 text-gray-900 "
                             "shadow-sm ring-1 ring-inset ring-gray-300 "
                             "placeholder:text-gray-400 focus:ring-2 focus:ring-inset "
                             "focus:ring-indigo-600 sm:text-sm sm:leading-6", })
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'rows': '3'})

            # for field_name, field in self.fields.items():
        #     # for the field budget i want it to display its balance attribute when it selected
        #     print("field_name", field_name)
        #
        #     field.widget.attrs.update({
        #         'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset "
        #                  "ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset "
        #                  "focus:ring-indigo-600"
        #                  "sm:text-sm sm:leading-6",
        #     })
        #     if field_name == 'budget_id':
        #         print('budget_id')
        #         field.widget.attrs.update({
        #             'class': "select2 block w-full rounded-md border-0 py-1.5 "
        #                      "text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 "
        #                      "placeholder:text-gray-400 focus:ring-2 focus:ring-inset "
        #                      "focus:ring-indigo-600 sm:text-sm sm:leading-6", })

        # if field is budgets display budget.balance on the label

        # if field_name == 'budget':
        #     choices = [(currency, currency) for currency in ['ZIG', 'USD']]
        #     field.choices = choices
        #     field.widget.attrs.update(
        #         {'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm '
        #                   'ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 '
        #                   'focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm '
        #                   'sm:leading-6'})
        #
        #
        #     if isinstance(field.widget, forms.Textarea):
        #         field.widget.attrs.update({'rows': '3'})
        #
        #     field.label = field.label or self.humanize_field_name(field_name)
        #     field.label_attrs = {'class': 'block text-sm font-medium leading-6 text-gray-900'}
        #
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


class ViramentForm(forms.ModelForm):
    class Meta:
        model = Asset_budget_Virament
        fields = '__all__'
        exclude = ['process', 'requested_by', 'virament_id', 'date_created', 'region'
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
    # 2: 'nd', 3

class AceReportForm(forms.ModelForm):
    end_date = forms.DateField(required=True, widget=forms.DateInput(attrs={'type': 'date'}))
    start_date = forms.DateField(required=True, widget=forms.DateInput(attrs={'type': 'date'}))
    class Meta:
        model = Ace2
        # add end date to fields

        fields = '__all__'
        exclude = ['process','requested_by','Ace_id', 'asset_number' , 'designation', 'Ace_id2',
                   'details_of_expenditure', 'quantity', 'total_connection_fee','capital_estimated', 'capital_sanctioned',
                   'present_tariff','present_fmc','capital_contribution','materials','connection_fee','labour','transport'
                    ,'classification','currency','amount','allocation_code_of_expenditure'
                   # include the project items
                   ]


    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        print("user", user)

        if user:
            user_profile = UserProfile.objects.filter(username=user.username).first()
            if user_profile:
                region = user_profile.region
                region_id = Regions.objects.filter(region=region).first()

                print("region", region)
                self.fields['budget_id'].queryset = AssetBudget.objects.filter(period=2024, region=region)
                self.fields['section'].queryset = Sections.objects.filter(region_id=region_id.id)
                #

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

            if (field_name == 'budget_id') or (field_name == 'section'):
                field.widget.attrs.update({
                    'class': "select2 block w-full rounded-md border-0 py-1.5 text-gray-900 "
                             "shadow-sm ring-1 ring-inset ring-gray-300 "
                             "placeholder:text-gray-400 focus:ring-2 focus:ring-inset "
                             "focus:ring-indigo-600 sm:text-sm sm:leading-6", })
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'rows': '3'})

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
    # 2: 'nd', 3

    def humanize_field_name(self, field_name):
        words = field_name.split('_')
        capitalized_words = [word.capitalize() for word in words]
        return ' '.join(capitalized_words)



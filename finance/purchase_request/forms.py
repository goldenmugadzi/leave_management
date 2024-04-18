from django import forms
from django.contrib.auth.models import User
from .models import *
from django.forms import formset_factory


class QuotationForm(forms.ModelForm):
    class Meta:
        model = Quotation
        fields = ['file']


QuotationFormSet = formset_factory(QuotationForm, extra=0, min_num=3, validate_min=True)


class PurchaseRequestForm(forms.ModelForm):
    class Meta:
        model = PurchaseRequest
        fields = '__all__'
        exclude = ['process', 'ace', 'requested_by']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset "
                         "ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 "
                         "sm:text-sm sm:leading-6",
            })

            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'rows': '3'})

class PrItemForm(forms.ModelForm):
    class Meta:
        model = PrItem
        fields = '__all__'
        exclude = ['purchase_request', 'ordered']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",
            })

            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'rows': '3'})

# PrItemFormSet = formset_factory(PrItemForm, extra=0, validate_min=True)


class QuoteItemForm(forms.ModelForm):
    class Meta:
        model = QuoteItem
        fields = '__all__'
        exclude = [ 'quotation']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",
            })
            # if field_name == 'pr_item':field.widget.attrs.update({'disabled': 'disabled'})    

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        initial_quantity = self.initial.get('quantity')

        if quantity > initial_quantity:
            raise forms.ValidationError(f"The quantity cannot be more than {initial_quantity}")

        return quantity
class acePurchaseRequestForm(forms.ModelForm):
    class Meta:
        model = PurchaseRequest
        fields = '__all__'
        exclude = ['process','requested_by']

    def __init__(self, *args, **kwargs):
        initial_data = kwargs.get('initial', {})

        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",
            })

            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'rows': '3'})

            field.label = field.label or self.humanize_field_name(field_name)
            field.label_attrs = {'class': 'block text-sm font-medium leading-6 text-gray-900'}


       
    def humanize_field_name(self, field_name):
        words = field_name.split('_')
        capitalized_words = [word.capitalize() for word in words]
        return ' '.join(capitalized_words)

    def get_quotation_label(self, quotation_number):
        suffix = 'th' if 11 <= quotation_number <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(quotation_number % 10, 'th')
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

class QuotationForm(forms.ModelForm):
    class Meta:
        model = Quotation
        fields = '__all__'
        exclude =['purchase_request',  'created_by']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",
            })

            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'rows': '3'})

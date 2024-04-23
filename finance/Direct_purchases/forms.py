from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from it.users.models import Roles
from .models import *
from django.forms import formset_factory


class DirectPurchaseForm(forms.ModelForm):
    class Meta:
        model = Direct_purchase
        fields = '__all__'
        exclude = ['process', 'requested_by', 'date_created', 'payment_status', 'grn_date',
                   'grn_delivery_status', 'payment_date', 'Dp_id']

    @login_required
    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset "
                         "ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 "
                         "sm:text-sm sm:leading-6",
            })

            if field_name == 'region':
                choices = [(region.id, region.region) for region in Regions.objects.all()]
                field.choices = choices
                field.widget.attrs.update({'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm '
                                                    'ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 '
                                                    'focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm '
                                                    'sm:leading-6'})

            if field_name == 'section':
                choices = [(section.id, section.section) for section in Sections.objects.all()]
                field.choices = choices
                field.widget.attrs.update({'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm '
                                                    'ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 '
                                                    'focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm '
                                                    'sm:leading-6'})

            if field_name == 'ace':
                choices = [(ace.Ace_id2, ace.details_of_expenditure) for ace in Ace.objects.all()]

                field.choices = choices
                field.widget.attrs.update({'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm '
                                                    'ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 '
                                                    'focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm '
                                                    'sm:leading-6'})

        if isinstance(field.widget, forms.Textarea):
            field.widget.attrs.update({'rows': '3'})

            field.label = field.label or self.humanize_field_name(field_name)
            field.label_attrs = {'class': 'block text-sm font-medium leading-6 text-gray-900'}

    def humanize_field_name(self, field_name):
        words = field_name.split('_')
        capitalized_words = [word.capitalize() for word in words]
        return ' '.join(capitalized_words)


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = '__all__'
        exclude = ['created_by', 'date_created']

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

            field.label = field.label or self.humanize_field_name(field_name)
            field.label_attrs = {'class': 'block text-sm font-medium leading-6 text-gray-900'}

    def humanize_field_name(self, field_name):
        words = field_name.split('_')
        capitalized_words = [word.capitalize() for word in words]
        return ' '.join(capitalized_words)


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = '__all__'

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

            field.label = field.label or self.humanize_field_name(field_name)
            field.label_attrs = {'class': 'block text-sm font-medium leading-6 text-gray-900'}
            if field_name == 'supplier':
                choices = [(supplier.id, supplier.name) for supplier in Supplier.objects.all()]
                field.choices = choices
                field.widget.attrs.update({'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm '
                                                    'ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 '
                                                    'focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm '
                                                    'sm:leading-6'})
            if field_name == 'direct_purchase':
                choices = [(direct_purchase.id, direct_purchase.id) for direct_purchase in
                           Direct_purchase.objects.all()]
                field.choices = choices
                field.widget.attrs.update({'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm '
                                                    'ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 '
                                                    'focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm '
                                                    'sm:leading-6'})
                field.label = field.label or field_name.replace('_', ' ').capitalize()
                field.label_attrs = {'class': 'block text-sm font-medium text-gray-900'}
            if field_name == 'price':
                field.widget.attrs.update({'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm '
                                                    'ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 '
                                                    'focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm '
                                                    'sm:leading-6'})
                field.label = field.label or field_name.replace('_', ' ').capitalize()
                field.label_attrs = {'class': 'block text-sm font-medium text-gray-900'}
            if field_name == 'quantity':
                field.widget.attrs.update({'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm '
                                                    'ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 '
                                                    'focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm '
                                                    'sm:leading-6'})
                field.label = field.label or field_name.replace('_', ' ').capitalize()
                field.label_attrs = {'class': 'block text-sm font-medium text-gray-900'}
            if field_name == 'total':
                field.widget.attrs.update({'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm '
                                                    'ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 '
                                                    'focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm '
                                                    'sm:leading-6'})
                field.label = field.label or field_name.replace('_', ' ').capitalize()
                field.label_attrs = {'class': 'block text-sm font-medium text-gray-900'}
                field.widget.attrs.update({'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm '
                                                    'ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 '
                                                    'focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm '
                                                    'sm:leading-6'})
            if field_name == 'description':
                field.widget.attrs.update({'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm '
                                                    'ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 '
                                                    'focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm '
                                                    'sm:leading-6'})
                field.label = field.label or field_name.replace('_', ' ').capitalize()
                field.label_attrs = {'class': 'block text-sm font-medium text-gray-900'}
            if field_name == 'unit':
                field.widget.attrs.update({'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm '
                                                    'ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 '
                                                    'focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm '
                                                    'sm:leading-6'})
                field.label = field.label or field_name.replace('_', ' ').capitalize()
                field.label_attrs = {'class': 'block text-sm font-medium text-gray-900'}
            if field_name == 'name':
                field.widget.attrs.update({'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm '
                                                    'ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 '
                                                    'focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm '
                                                    'sm:leading-6'})
                field.label = field.label or field_name.replace('_', ' ').capitalize()
                field.label_attrs = {'class': 'block text-sm font-medium text-gray-900'}
                field.widget.attrs.update({'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm '
                                                    'ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 '
                                                    'focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm '
                                                    'sm:leading-6'})
            if field_name == 'supplier':
                choices = [(supplier.id, supplier.name) for supplier in Supplier.objects.all()]
                field.choices = choices
                field.widget.attrs.update({'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm '
                                                    'ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 '
                                                    'focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm '
                                                    'sm:leading-6'})
                field.label = field.label or field_name.replace('_', ' ').capitalize()
                field.label_attrs = {'class': 'block text-sm font-medium text-gray-900'}
            if field_name == 'direct_purchase':
                choices = [(direct_purchase.id, direct_purchase.id) for direct_purchase in
                           Direct_purchase.objects.all()]
                field.choices = choices
                field.widget.attrs.update({'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm '
                                                    'ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 '
                                                    'focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm '
                                                    'sm:leading-6'})
                field.label = field.label or field_name.replace('_', ' ').capitalize()
                field.label_attrs = {'class': 'block text-sm font-medium text-gray-900'}

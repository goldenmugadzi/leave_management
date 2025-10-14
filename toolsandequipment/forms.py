from django import forms
from .models import ToolOrEquipment, ToolsAndEquipmentRegister, ToolsAndEquipmentRegisterItem, Remarks

FIELD_CSS_CLASSES = "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"

class ToolOrEquipmentForm(forms.ModelForm):
    class Meta:
        model = ToolOrEquipment
        fields = ['name', 'total_quantity', 'value', 'asset_number']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            classes = FIELD_CSS_CLASSES
            if isinstance(field, forms.ModelChoiceField):
                classes += ' select2'
            field.widget.attrs.update({'class': classes})
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'rows': '3'})

class ToolsAndEquipmentRegisterForm(forms.ModelForm):
    class Meta:
        model = ToolsAndEquipmentRegister
        fields = ['artisan', 'undertaking', ]

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            region = getattr(user, 'region', None)
            if region is not None:
                self.fields['undertaking'].queryset = self.fields['undertaking'].queryset.filter(region=region)
        for field_name, field in self.fields.items():
            classes = FIELD_CSS_CLASSES
            if field_name in ['artisan', 'undertaking']:
                classes += ' select2'
            field.widget.attrs.update({'class': classes})
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'rows': '3'})

class ToolsAndEquipmentRegisterItemForm(forms.ModelForm):
    class Meta:
        model = ToolsAndEquipmentRegisterItem
        fields = ['tool_or_equipment', 'quantity', 'value', 'so_or_invoice_no', 'so_or_invoice_date', 'initials', 'remarks']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            classes = FIELD_CSS_CLASSES
            if field_name in ['tool_or_equipment']:
                classes += ' select2'
            field.widget.attrs.update({'class': classes})
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'rows': '2'})

class RemarksForm(forms.ModelForm):
    class Meta:
        model = Remarks
        fields = ['comment', 'author']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            classes = FIELD_CSS_CLASSES
            if isinstance(field, forms.ModelChoiceField):
                classes += ' select2'
            field.widget.attrs.update({'class': classes})
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'rows': '3'})

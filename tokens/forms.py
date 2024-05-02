from django import forms
from .models import Meter, Customer, Token, REIMBURSEMENT, CLEARCREDIT, TAMPERTOKEN, OldToken, FaultMeter, RecoveredMeter, FaultMaintanance, Reconnection

class MeterForm(forms.ModelForm):
    class Meta:
        model = Meter
        fields = "__all__"
        # fields = ['number', 'kilowatt_hours', 'phase']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",})
            if isinstance(field.widget, forms.Textarea):field.widget.attrs.update({'rows': '3'})

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = "__all__"
        # fields = ['name', 'address', 'stand_number', 'contact_number']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",})
            if isinstance(field.widget, forms.Textarea):field.widget.attrs.update({'rows': '3'})

class TokenForm(forms.ModelForm):
    class Meta:
        model = Token
        fields = "__all__"
        exclude = [ 'meter', 'customer', 'created_by', 'created_at', 'process',]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",})
            if isinstance(field.widget, forms.Textarea):field.widget.attrs.update({'rows': '3'})
class ReimbursementForm(forms.ModelForm):
    class Meta:
        model = REIMBURSEMENT
        fields = "__all__"
        exclude = ['token']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",})
            if isinstance(field.widget, forms.Textarea):field.widget.attrs.update({'rows': '3'})

class ClearCreditForm(forms.ModelForm):
    class Meta:
        model = CLEARCREDIT
        fields = "__all__"
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",})
            if isinstance(field.widget, forms.Textarea):field.widget.attrs.update({'rows': '3'})

class TamperTokenForm(forms.ModelForm):
    class Meta:
        model = TAMPERTOKEN
        fields = ['token', 'purpose']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",})
            if isinstance(field.widget, forms.Textarea):field.widget.attrs.update({'rows': '3'})

class OldTokenForm(forms.ModelForm):
    class Meta:
        model = OldToken
        fields = ['old_token', 'reimbursement']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",})
            if isinstance(field.widget, forms.Textarea):field.widget.attrs.update({'rows': '3'})

class FaultMeterForm(forms.ModelForm):
    class Meta:
        model = FaultMeter
        fields = ['reimbursement', 'units', 'photo']

class RecoveredMeterForm(forms.ModelForm):
    class Meta:
        model = RecoveredMeter
        fields = ['token', 'photo']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",})
            if isinstance(field.widget, forms.Textarea):field.widget.attrs.update({'rows': '3'})

class FaultMaintananceForm(forms.ModelForm):
    class Meta:
        model = FaultMaintanance
        fields = ['photo', 'units']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",})
            if isinstance(field.widget, forms.Textarea):field.widget.attrs.update({'rows': '3'})
class ReconnectionForm(forms.ModelForm):
    class Meta:
        model = Reconnection
        fields = ['invoice', 'proof_of_payment']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",})
            if isinstance(field.widget, forms.Textarea):field.widget.attrs.update({'rows': '3'})

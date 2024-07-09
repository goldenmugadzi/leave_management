from django import forms
from .models import Meter, Customer, Token, REIMBURSEMENT, CLEARCREDIT, TAMPERTOKEN, OldToken, FaultMeter, RecoveredMeter, FaultMaintanance, Reconnection

class MeterForm(forms.ModelForm):
    class Meta:
        model = Meter
        fields = "__all__"
        # fields = ['number', 'kilowatt_hours', 'phase']
    def clean_number(self):
        number = self.cleaned_data['number']
        if len(number) != 11 or not number.isdigit():
            raise forms.ValidationError('Enter a valid Meter number.')
        return number
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
class GenerateTokenForm(forms.ModelForm):
    class Meta:
        model = Token
        fields = ('token_photo',  )
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",
            })
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'rows': '3'})
    def clean_token_photo(self):
        token_photo = self.cleaned_data['token_photo']
        if not token_photo:
            raise forms.ValidationError('A token photo is required.')
        return token_photo
class TokenForm(forms.ModelForm):
    class Meta:
        model = Token
        fields = "__all__"
        exclude = [ 'meter', 'customer','token_photo' , 'created_by','region', 'created_at', 'process',]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",})
            if isinstance(field.widget, forms.Textarea):field.widget.attrs.update({'rows': '3'})
            if field_name == 'cost_center':
                field.widget.attrs.update({'class': "select2 block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",})
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
        fields ="__all__"
        exclude=['token']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",})
            if isinstance(field.widget, forms.Textarea):field.widget.attrs.update({'rows': '3'})
    def clean_receipt(self):
        receipt = self.cleaned_data['receipt']
        if not receipt:
            raise forms.ValidationError('A receipt photo is required.')
        return receipt
   
class TamperTokenForm(forms.ModelForm):
    class Meta:
        model = TAMPERTOKEN
        fields = "__all__"
        exclude=['token']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",})
            if isinstance(field.widget, forms.Textarea):field.widget.attrs.update({'rows': '3'})
class OldTokenForm(forms.ModelForm):
    class Meta:
        model = OldToken
        fields = "__all__"
        exclude=['token']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",})
            if isinstance(field.widget, forms.Textarea):field.widget.attrs.update({'rows': '3'})
    def clean_old_token(self):
        old_token = self.cleaned_data['old_token']
        if not old_token:
            raise forms.ValidationError('A old token photo is required.')
        return old_token
   
class FaultMeterForm(forms.ModelForm):
    class Meta:
        model = FaultMeter
        fields = "__all__"
        exclude=['token']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",})
            if isinstance(field.widget, forms.Textarea):field.widget.attrs.update({'rows': '3'})
    def clean_photo(self):
        photo = self.cleaned_data['photo']
        if not photo:
            raise forms.ValidationError('A photo  is required.')
        return photo
   
class RecoveredMeterForm(forms.ModelForm):
    class Meta:
        model = RecoveredMeter
        fields ="__all__"
        exclude=['token']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",})
            if isinstance(field.widget, forms.Textarea):field.widget.attrs.update({'rows': '3'})
    def clean_picture(self):
        picture = self.cleaned_data['picture']
        if not picture:
            raise forms.ValidationError('A picture  is required.')
        return picture
   
class FaultMaintananceForm(forms.ModelForm):
    class Meta:
        model = FaultMaintanance
        fields ="__all__"
        exclude=['token']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",})
            if isinstance(field.widget, forms.Textarea):field.widget.attrs.update({'rows': '3'})
class ReconnectionForm(forms.ModelForm):
    class Meta:
        model = Reconnection
        fields ="__all__"
        exclude=['token']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",})
            if isinstance(field.widget, forms.Textarea):field.widget.attrs.update({'rows': '3'})
    def clean_invoice(self):
        invoice = self.cleaned_data['invoice']
        if not invoice:
            raise forms.ValidationError('A invoice photo is required.')
        return invoice
    def clean_proof_of_payment(self):
        proof_of_payment = self.cleaned_data['proof_of_payment']
        if not proof_of_payment:
            raise forms.ValidationError('A proof_of_payment photo is required.')
        return proof_of_payment
from django import forms
from .models import Customer, DocumentType

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            'customer_id', 'name', 'address', 'stand_number', 
            'contact_number', 'email', 'customer_type', 
            'account_number', 'meter_number', 'is_active'
        ]
        widgets = {
            'customer_id': forms.TextInput(attrs={'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6'}),
            'name': forms.TextInput(attrs={'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6'}),
            'address': forms.TextInput(attrs={'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6'}),
            'stand_number': forms.TextInput(attrs={'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6'}),
            'contact_number': forms.TextInput(attrs={'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6'}),
            'email': forms.EmailInput(attrs={'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6'}),
            'customer_type': forms.Select(attrs={'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6'}),
            'account_number': forms.TextInput(attrs={'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6'}),
            'meter_number': forms.TextInput(attrs={'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-600'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add help text for customer_id
        self.fields['customer_id'].help_text = "Unique identifier for this customer"
        self.fields['customer_id'].required = True
        
        # Make customer_id readonly when editing existing customer
        if self.instance.pk:  # If this is an existing customer
            self.fields['customer_id'].widget.attrs['readonly'] = True
            self.fields['customer_id'].help_text = "Customer ID cannot be changed once created"
        
        # Add placeholder texts
        self.fields['name'].widget.attrs.update({'placeholder': 'Customer name'})
        self.fields['address'].widget.attrs.update({'placeholder': 'Physical address'})
        self.fields['stand_number'].widget.attrs.update({'placeholder': 'Stand number (optional)'})
        self.fields['contact_number'].widget.attrs.update({'placeholder': 'Phone number'})
        self.fields['email'].widget.attrs.update({'placeholder': 'Email address'})
        self.fields['account_number'].widget.attrs.update({'placeholder': 'Account number (optional)'})
        self.fields['meter_number'].widget.attrs.update({'placeholder': 'Meter number (optional)'})
        
        # Make is_active checked by default for new customers
        if not self.instance.pk:  # If this is a new customer
            self.fields['is_active'].initial = True 

class DocumentTypeForm(forms.ModelForm):
    class Meta:
        model = DocumentType
        fields = ['name', 'description', 'required']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6'}),
            'required': forms.CheckboxInput(attrs={'class': 'h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-600'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.update({'placeholder': 'Document type name'})
        self.fields['description'].widget.attrs.update({'placeholder': 'Description (optional)'})
        self.fields['name'].help_text = "Enter a unique name for this document type"
        self.fields['required'].help_text = "Check if this document is required for customer onboarding" 
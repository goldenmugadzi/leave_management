from django import forms
from django.core.exceptions import ValidationError
from .models import ClientApplication, InspectionReport, ApplicationAssignment


class ClientApplicationForm(forms.ModelForm):
    """Form for creating and editing client applications"""
    
    class Meta:
        model = ClientApplication
        fields = [
            'application_type', 'priority', 'customer_name', 'customer_phone',
            'customer_email', 'customer_address', 'property_address', 'property_type',
            'service_number', 'installation_description', 'contractor_name',
            'contractor_license', 'notes', 'documents_attached'
        ]
        
        widgets = {
            'application_type': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'customer_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter customer name'}),
            'customer_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+263 xxx xxx xxx'}),
            'customer_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'customer@example.com'}),
            'customer_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'property_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'property_type': forms.Select(attrs={'class': 'form-control'}),
            'service_number': forms.TextInput(attrs={'class': 'form-control'}),
            'installation_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'contractor_name': forms.TextInput(attrs={'class': 'form-control'}),
            'contractor_license': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'documents_attached': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class InspectionReportForm(forms.ModelForm):
    """Form for creating and editing inspection reports"""
    
    class Meta:
        model = InspectionReport
        fields = [
            'inspection_date', 'service_no', 'installation_type', 'consumer_name',
            'property_supplied', 'property_owner_name', 'property_owner_address',
            'contractor', 'contractor_address', 'size_of_mains', 'size_of_mains_conduit',
            'earthing', 'consumer_unit_type', 'db_enclosure_type',
            'insulation_resistance_between', 'insulation_resistance_to_earth',
            'continuity_test', 'earth_fault_protection', 'overcurrent_protection',
            'installation_safety', 'conduit_material', 'conduit_installation',
            'overall_compliance', 'defects_found', 'inspector_comments'
        ]
        
        widgets = {
            'inspection_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'service_no': forms.TextInput(attrs={'class': 'form-control'}),
            'installation_type': forms.Select(attrs={'class': 'form-control'}),
            'consumer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'property_supplied': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'property_owner_name': forms.TextInput(attrs={'class': 'form-control'}),
            'property_owner_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'contractor': forms.TextInput(attrs={'class': 'form-control'}),
            'contractor_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'size_of_mains': forms.TextInput(attrs={'class': 'form-control'}),
            'size_of_mains_conduit': forms.TextInput(attrs={'class': 'form-control'}),
            'earthing': forms.TextInput(attrs={'class': 'form-control'}),
            'consumer_unit_type': forms.Select(attrs={'class': 'form-control'}),
            'db_enclosure_type': forms.Select(attrs={'class': 'form-control'}),
            'insulation_resistance_between': forms.TextInput(attrs={'class': 'form-control'}),
            'insulation_resistance_to_earth': forms.TextInput(attrs={'class': 'form-control'}),
            'continuity_test': forms.TextInput(attrs={'class': 'form-control'}),
            'earth_fault_protection': forms.Select(attrs={'class': 'form-control'}),
            'overcurrent_protection': forms.Select(attrs={'class': 'form-control'}),
            'installation_safety': forms.Select(attrs={'class': 'form-control'}),
            'conduit_material': forms.Select(attrs={'class': 'form-control'}),
            'conduit_installation': forms.Select(attrs={'class': 'form-control'}),
            'overall_compliance': forms.Select(attrs={'class': 'form-control'}),
            'defects_found': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'inspector_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }


class ApplicationAssignmentForm(forms.ModelForm):
    """Form for assigning applications to field officers"""
    
    class Meta:
        model = ApplicationAssignment
        fields = ['application', 'assigned_to', 'due_date', 'assignment_notes']
        
        widgets = {
            'application': forms.Select(attrs={'class': 'form-control'}),
            'assigned_to': forms.Select(attrs={'class': 'form-control'}),
            'due_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'assignment_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter applications to only show submitted ones
        self.fields['application'].queryset = ClientApplication.objects.filter(status='submitted')
        
        # Filter users to show only active ones
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.fields['assigned_to'].queryset = User.objects.filter(is_active=True)


class InspectionSearchForm(forms.Form):
    """Form for searching and filtering inspections"""
    
    search_query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Search applications, customers, service numbers...'
        })
    )
    
    application_type = forms.ChoiceField(
        choices=[('', 'All Types')] + ClientApplication.APPLICATION_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + ClientApplication.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    ) 
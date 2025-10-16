from django import forms
from django.core.exceptions import ValidationError
from .models import Equipment, EquipmentOperation, OperationDocument


class EquipmentForm(forms.ModelForm):
    """
    Form for creating and editing equipment
    """
    
    class Meta:
        model = Equipment
        fields = [
            'equipment_type', 'make', 'serial_number', 'kva_rating', 
            'ampere_rating', 'voltage_rating', 'installation_date',
            'status', 'location_description', 'substation_name', 
            'section', 'district'
        ]
        widgets = {
            'installation_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'location_description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'equipment_type': forms.Select(attrs={'class': 'form-control'}),
            'make': forms.TextInput(attrs={'class': 'form-control'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control'}),
            'kva_rating': forms.NumberInput(attrs={'class': 'form-control'}),
            'ampere_rating': forms.NumberInput(attrs={'class': 'form-control'}),
            'voltage_rating': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'substation_name': forms.TextInput(attrs={'class': 'form-control'}),
            'section': forms.TextInput(attrs={'class': 'form-control'}),
            'district': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make certain fields required
        self.fields['equipment_type'].required = True
        self.fields['make'].required = True
        self.fields['serial_number'].required = True
        self.fields['voltage_rating'].required = True
        self.fields['substation_name'].required = True
        self.fields['district'].required = True
        
        # Add help text
        self.fields['serial_number'].help_text = 'Must be unique across all equipment'
        self.fields['voltage_rating'].help_text = 'e.g., 11kV, 33kV, 132kV'
    
    def clean_serial_number(self):
        serial_number = self.cleaned_data.get('serial_number')
        if serial_number:
            # Check for uniqueness (excluding current instance if editing)
            qs = Equipment.objects.filter(serial_number=serial_number)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError('Equipment with this serial number already exists.')
        return serial_number


class EquipmentOperationForm(forms.ModelForm):
    """
    Form for creating and editing equipment operations (Form E114)
    """
    
    class Meta:
        model = EquipmentOperation
        fields = [
            'operation_type', 'consumer_name', 'consumer_account_number',
            'substation_name', 'section', 'district', 'equipment_installed',
            'equipment_removed', 'reason', 'operator_name', 'operator_designation',
            'operation_date', 'scheduled_date', 'priority', 'estimated_duration_hours',
            'cost_estimate'
        ]
        widgets = {
            'operation_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'scheduled_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'operation_type': forms.Select(attrs={'class': 'form-control'}),
            'consumer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'consumer_account_number': forms.TextInput(attrs={'class': 'form-control'}),
            'substation_name': forms.TextInput(attrs={'class': 'form-control'}),
            'section': forms.TextInput(attrs={'class': 'form-control'}),
            'district': forms.TextInput(attrs={'class': 'form-control'}),
            'equipment_installed': forms.Select(attrs={'class': 'form-control'}),
            'equipment_removed': forms.Select(attrs={'class': 'form-control'}),
            'operator_name': forms.TextInput(attrs={'class': 'form-control'}),
            'operator_designation': forms.TextInput(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'estimated_duration_hours': forms.NumberInput(attrs={'class': 'form-control'}),
            'cost_estimate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Limit equipment choices to active equipment
        self.fields['equipment_installed'].queryset = Equipment.objects.filter(status='active')
        self.fields['equipment_removed'].queryset = Equipment.objects.filter(status='active')
        
        # Make certain fields required
        self.fields['operation_type'].required = True
        self.fields['consumer_name'].required = True
        self.fields['substation_name'].required = True
        self.fields['district'].required = True
        self.fields['reason'].required = True
        self.fields['operator_name'].required = True
        self.fields['operator_designation'].required = True
        
        # Add help text
        self.fields['consumer_account_number'].help_text = 'Optional - consumer account number if applicable'
        self.fields['estimated_duration_hours'].help_text = 'Estimated time to complete the operation'
        self.fields['cost_estimate'].help_text = 'Estimated cost in USD'
    
    def clean(self):
        cleaned_data = super().clean()
        operation_type = cleaned_data.get('operation_type')
        equipment_installed = cleaned_data.get('equipment_installed')
        equipment_removed = cleaned_data.get('equipment_removed')
        
        # Validation based on operation type
        if operation_type == 'installation' and not equipment_installed:
            raise ValidationError('Equipment to be installed is required for installation operations.')
            
        if operation_type == 'removal' and not equipment_removed:
            raise ValidationError('Equipment to be removed is required for removal operations.')
            
        if operation_type == 'change' and (not equipment_installed or not equipment_removed):
            raise ValidationError('Both equipment to be installed and removed are required for change operations.')
            
        # Ensure equipment installed and removed are not the same
        if equipment_installed and equipment_removed and equipment_installed == equipment_removed:
            raise ValidationError('Equipment to be installed and removed cannot be the same.')
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Set status based on which submit button was clicked
        if 'submit_and_send' in self.data:
            instance.status = 'submitted'
        else:
            instance.status = 'draft'
            
        if commit:
            instance.save()
        return instance


class OperationDocumentForm(forms.ModelForm):
    """
    Form for uploading documents related to operations
    """
    
    class Meta:
        model = OperationDocument
        fields = ['document_type', 'file', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'document_type': forms.Select(attrs={'class': 'form-control'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make certain fields required
        self.fields['document_type'].required = True
        self.fields['file'].required = True
        
        # Add help text
        self.fields['file'].help_text = 'Supported formats: PDF, JPG, PNG, DOC, DOCX (Max size: 10MB)'
        self.fields['description'].help_text = 'Optional description of the document'
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Check file size (10MB limit)
            if file.size > 10 * 1024 * 1024:
                raise ValidationError('File size cannot exceed 10MB.')
            
            # Check file extension
            allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx']
            file_extension = file.name.lower().split('.')[-1]
            if f'.{file_extension}' not in allowed_extensions:
                raise ValidationError('File type not supported. Allowed types: PDF, JPG, PNG, DOC, DOCX')
        
        return file


class EquipmentSearchForm(forms.Form):
    """
    Form for searching and filtering equipment
    """
    search = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by serial number, make, or substation...'
        })
    )
    equipment_type = forms.ChoiceField(
        choices=[('', 'All Types')] + Equipment.EQUIPMENT_TYPES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + Equipment.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    district = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'District...'
        })
    )


class OperationSearchForm(forms.Form):
    """
    Form for searching and filtering operations
    """
    search = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by form number, consumer, or operator...'
        })
    )
    operation_type = forms.ChoiceField(
        choices=[('', 'All Types')] + EquipmentOperation.OPERATION_TYPES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + EquipmentOperation.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )

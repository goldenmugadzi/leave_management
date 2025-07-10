from django import forms
from django.core.exceptions import ValidationError
from .models import CircuitBreaker, MaintenanceRecord
import re

class CircuitBreakerForm(forms.ModelForm):
    class Meta:
        model = CircuitBreaker
        fields = '__all__'
        widgets = {
            'breaker_number': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'e.g., CB-001, BR-132-01',
                'pattern': '[A-Za-z0-9-]+',
                'title': 'Use letters, numbers, and hyphens only'
            }),
            'make_type': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'e.g., ABB SF6, Siemens 3AP1',
                'list': 'make_types'
            }),
            'voltage_capacity': forms.Select(attrs={'class': 'form-control'}),
            'serial_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Manufacturer serial number'
            }),
            'installation_date': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control',
                'max': '9999-12-31'  # Prevent future dates that are too far
            }),
            'sub_station': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'e.g., Main Substation, Industrial Complex',
                'list': 'substations'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    # Custom voltage capacity choices
    VOLTAGE_CHOICES = [
        ('', 'Select Voltage Capacity'),
        ('11kV', '11kV'),
        ('22kV', '22kV'),
        ('33kV', '33kV'),
        ('66kV', '66kV'),
        ('88kV', '88kV'),
        ('132kV', '132kV'),
        ('220kV', '220kV'),
        ('330kV', '330kV'),
        ('400kV', '400kV'),
    ]
    
    voltage_capacity = forms.ChoiceField(
        choices=VOLTAGE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make required fields more obvious
        required_fields = ['breaker_number', 'make_type', 'voltage_capacity', 'serial_number', 'sub_station']
        for field_name in required_fields:
            self.fields[field_name].widget.attrs.update({'required': True})
            self.fields[field_name].label = f"{self.fields[field_name].label} *"
        
        # Add help texts
        self.fields['breaker_number'].help_text = "Unique identifier for the circuit breaker"
        self.fields['serial_number'].help_text = "Manufacturer's serial number"
        self.fields['installation_date'].help_text = "Date when the circuit breaker was installed"
        
        # Set initial value for is_active
        if not self.instance.pk:  # New instance
            self.fields['is_active'].initial = True
    
    def clean_breaker_number(self):
        """Validate breaker number format and uniqueness"""
        breaker_number = self.cleaned_data.get('breaker_number')
        
        if breaker_number:
            # Check format (letters, numbers, hyphens only)
            if not re.match(r'^[A-Za-z0-9-]+$', breaker_number):
                raise ValidationError("Breaker number can only contain letters, numbers, and hyphens.")
            
            # Check uniqueness (excluding current instance for updates)
            existing = CircuitBreaker.objects.filter(breaker_number__iexact=breaker_number)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise ValidationError("A circuit breaker with this number already exists.")
        
        return breaker_number.upper() if breaker_number else breaker_number
    
    def clean_serial_number(self):
        """Validate serial number uniqueness"""
        serial_number = self.cleaned_data.get('serial_number')
        
        if serial_number:
            # Check uniqueness (excluding current instance for updates)
            existing = CircuitBreaker.objects.filter(serial_number__iexact=serial_number)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise ValidationError("A circuit breaker with this serial number already exists.")
        
        return serial_number
    
    def clean_installation_date(self):
        """Validate installation date"""
        installation_date = self.cleaned_data.get('installation_date')
        
        if installation_date:
            from django.utils import timezone
            today = timezone.now().date()
            
            # Check if date is not in the future
            if installation_date > today:
                raise ValidationError("Installation date cannot be in the future.")
            
            # Check if date is not too old (e.g., before 1950)
            if installation_date.year < 1950:
                raise ValidationError("Installation date seems too old. Please verify.")
        
        return installation_date

class CircuitBreakerBulkImportForm(forms.Form):
    """Form for bulk importing circuit breakers from CSV/Excel"""
    file = forms.FileField(
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': '.csv,.xlsx,.xls'
        }),
        help_text="Upload CSV or Excel file with circuit breaker data"
    )
    
    skip_duplicates = forms.BooleanField(
        required=False,
        initial=True,
        help_text="Skip records with duplicate breaker numbers or serial numbers"
    )
    
    def clean_file(self):
        """Validate uploaded file"""
        file = self.cleaned_data.get('file')
        
        if file:
            # Check file size (max 5MB)
            if file.size > 5 * 1024 * 1024:
                raise ValidationError("File size cannot exceed 5MB.")
            
            # Check file extension
            allowed_extensions = ['.csv', '.xlsx', '.xls']
            file_extension = f".{file.name.split('.')[-1].lower()}"
            
            if file_extension not in allowed_extensions:
                raise ValidationError("Only CSV and Excel files are allowed.")
        
        return file

class QuickCircuitBreakerForm(forms.ModelForm):
    """Simplified form for quick circuit breaker creation"""
    class Meta:
        model = CircuitBreaker
        fields = ['breaker_number', 'sub_station', 'make_type', 'voltage_capacity']
        widgets = {
            'breaker_number': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'CB-001',
                'required': True
            }),
            'sub_station': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Substation Name',
                'list': 'substations',
                'required': True
            }),
            'make_type': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'ABB, Siemens, etc.',
                'list': 'make_types',
                'required': True
            }),
            'voltage_capacity': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
        }
    
    voltage_capacity = forms.ChoiceField(
        choices=CircuitBreakerForm.VOLTAGE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )
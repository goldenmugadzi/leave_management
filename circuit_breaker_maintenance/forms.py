from django import forms
from django.core.exceptions import ValidationError
from .models import (
    CircuitBreaker, MaintenanceRecord, InsulationResistanceTest, 
    ContactResistanceTest, TimingTest, InterlockTest, ContactTravelTest,
    DuctorTest, ProtectionTest, RelayOperationTest, AutoRecloseTest,
    VacuumBreakerChecks, OilBreakerChecks, TransformerMaintenanceRecord,
    TransformerCheckItem
)
import re

class CircuitBreakerForm(forms.ModelForm):
    # Override region field to use ModelChoiceField
    region = forms.ModelChoiceField(
        queryset=None,  # Will be set in __init__
        empty_label="Select a region",
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
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
            'breaker_type': forms.Select(attrs={'class': 'form-control'}),
            'make_type': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'e.g., ABB SF6, Siemens 3AP1',
                'list': 'make_types'
            }),
            'voltage_capacity': forms.Select(attrs={'class': 'form-control'}),
            'current_rating': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 1000A, 2000A'
            }),
            'breaking_capacity': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 31.5kA, 40kA'
            }),
            'serial_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Manufacturer serial number'
            }),
            'installation_date': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control',
                'max': '2024-12-31'  # Prevent future dates
            }),
            'sub_station': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter substation name',
                'list': 'substations'
            }),
            'bay_position': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Bay 1, Feeder 3'
            }),
            # V/T fields
            'vt_make_type': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'V/T Make/Type'
            }),
            'vt_volt_ratio_rating': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 132kV/110V'
            }),
            'vt_serial_no': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'V/T Serial Number'
            }),
            # C/T fields
            'ct_make_type': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'C/T Make/Type'
            }),
            'ct_ratio': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 600/5A, 1000/1A'
            }),
            'ct_serial_no': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'C/T Serial Number'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'})
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
        # Set region queryset
        try:
            from it.users.models import Regions
            self.fields['region'].queryset = Regions.objects.all()
        except ImportError:
            # If the users app is not available, hide the region field
            del self.fields['region']
        
        # Make form fields more user-friendly
        self.fields['breaker_number'].help_text = "Unique identifier for the circuit breaker"
        self.fields['serial_number'].help_text = "Manufacturer's serial number"
        self.fields['breaker_type'].help_text = "Select the type of circuit breaker"
        
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
        label="Upload File",
        help_text="Upload a CSV or Excel file with circuit breaker data. Required columns: breaker_number, sub_station, make_type, voltage_capacity",
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv,.xlsx,.xls'
        })
    )
    
    skip_duplicates = forms.BooleanField(
        label="Skip Duplicates",
        help_text="Skip records that already exist instead of showing error",
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
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


class MaintenanceRecordForm(forms.ModelForm):
    """Comprehensive form for creating and editing maintenance records"""
    
    class Meta:
        model = MaintenanceRecord
        exclude = ['id', 'report_no', 'created_at', 'updated_at', 'created_by', 'updated_by']
        widgets = {
            'circuit_breaker': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'required': True
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-control'
            }),
            'permit_to_work_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'PTW-001'
            }),
            'permit_issued_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            'permit_expires_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            'sanction_for_test_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'SFT-001'
            }),
            'limitation_of_access_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'LOA-001'
            }),
            'operations_since_last_oh': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'operations_counter_last_oh': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'operations_counter_to_date': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'previous_report_no': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Previous maintenance report number'
            }),
            'previous_report_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'equipment_details': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter equipment details as JSON or structured text'
            }),
            'general_checks': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': 'Enter general checks as JSON or structured text'
            }),
            'mechanism_checks': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Enter mechanism checks as JSON or structured text'
            }),
            'ct_checks': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Enter C/T checks as JSON or structured text'
            }),
            'vt_checks': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Enter V/T checks as JSON or structured text'
            }),
            'test_results': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': 'Enter test results as JSON or structured text'
            }),
            'weather_conditions': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Clear, Rainy, Humid'
            }),
            'ambient_temperature': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'placeholder': 'Temperature in °C'
            }),
            'humidity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 100,
                'placeholder': 'Humidity percentage'
            }),
            'safety_precautions_taken': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter safety precautions as JSON or structured text'
            }),
            'environmental_considerations': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Environmental considerations and impact'
            }),
            'maintenance_team': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter maintenance team details as JSON or structured text'
            }),
            'maintenance_carried_out_by': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Technician name or team lead'
            }),
            'protection_test_carried_out_by': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Protection engineer name'
            }),
            'checked_by': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Checker name'
            }),
            'checked_by_role': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Senior Technician'
            }),
            'checked_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            'approved_by': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Approver name'
            }),
            'approved_by_role': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Maintenance Manager'
            }),
            'approved_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            'remarks': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Additional remarks and observations'
            }),
            'recommendations': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Recommendations for future maintenance'
            }),
            'follow_up_required': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'follow_up_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'next_maintenance_due': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'maintenance_interval_months': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 60,
                'value': 12
            })
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        circuit_breaker_id = kwargs.pop('circuit_breaker_id', None)
        super().__init__(*args, **kwargs)
        
        # Set circuit breaker if provided
        if circuit_breaker_id and not self.instance.pk:
            try:
                circuit_breaker = CircuitBreaker.objects.get(pk=circuit_breaker_id)
                self.fields['circuit_breaker'].initial = circuit_breaker
                # Optionally make it readonly if circuit breaker is preselected
                self.fields['circuit_breaker'].widget.attrs['readonly'] = True
            except CircuitBreaker.DoesNotExist:
                pass
        
        # Filter circuit breakers to only active ones
        self.fields['circuit_breaker'].queryset = CircuitBreaker.objects.filter(
            is_active=True
        ).order_by('breaker_number')
        
        # Set default values for new records
        if not self.instance.pk:
            from django.utils import timezone
            self.fields['date'].initial = timezone.now().date()
            self.fields['general_checks'].initial = MaintenanceRecord.get_default_general_checks()
            self.fields['test_results'].initial = MaintenanceRecord.get_default_test_results()
    
    def clean_date(self):
        """Validate maintenance date"""
        date = self.cleaned_data.get('date')
        
        if date:
            from django.utils import timezone
            today = timezone.now().date()
            
            # Date cannot be in the future beyond today
            if date > today:
                raise ValidationError("Maintenance date cannot be in the future.")
            
            # Date should not be too old (e.g., more than 2 years ago)
            import datetime
            two_years_ago = today - datetime.timedelta(days=730)
            if date < two_years_ago:
                raise ValidationError("Maintenance date seems too old. Please verify.")
        
        return date
    
    def clean_follow_up_date(self):
        """Validate follow-up date"""
        follow_up_date = self.cleaned_data.get('follow_up_date')
        follow_up_required = self.cleaned_data.get('follow_up_required')
        
        if follow_up_required and not follow_up_date:
            raise ValidationError("Follow-up date is required when follow-up is marked as required.")
        
        if follow_up_date:
            from django.utils import timezone
            today = timezone.now().date()
            
            if follow_up_date <= today:
                raise ValidationError("Follow-up date should be in the future.")
        
        return follow_up_date
    
    def clean_next_maintenance_due(self):
        """Validate next maintenance due date"""
        next_due = self.cleaned_data.get('next_maintenance_due')
        maintenance_date = self.cleaned_data.get('date')
        
        if next_due and maintenance_date:
            if next_due <= maintenance_date:
                raise ValidationError("Next maintenance due date should be after the current maintenance date.")
        
        return next_due
    
    def clean_general_checks(self):
        """Clean and convert general_checks to JSON format, accepting both JSON and plain text"""
        general_checks = self.cleaned_data.get('general_checks')
        
        if not general_checks:
            return []
        
        # If it's already a list or dict, return as is
        if isinstance(general_checks, (list, dict)):
            return general_checks
        
        # Try to parse as JSON first
        if isinstance(general_checks, str):
            general_checks = general_checks.strip()
            if not general_checks:
                return []
            
            # Try JSON parsing
            try:
                import json
                parsed = json.loads(general_checks)
                return parsed if isinstance(parsed, (list, dict)) else [str(parsed)]
            except (json.JSONDecodeError, ValueError):
                # If JSON parsing fails, treat as plain text
                # Convert plain text to a structured format
                lines = [line.strip() for line in general_checks.split('\n') if line.strip()]
                if len(lines) == 1:
                    # Single line - could be comma-separated items
                    items = [item.strip() for item in lines[0].split(',') if item.strip()]
                    if len(items) > 1:
                        return items
                    else:
                        return [lines[0]]
                else:
                    # Multiple lines - each line is an item
                    return lines
        
        return []
    
    def clean_test_results(self):
        """Clean and convert test_results to JSON format, accepting both JSON and plain text"""
        test_results = self.cleaned_data.get('test_results')
        
        if not test_results:
            return {}
        
        # If it's already a dict or list, return as is
        if isinstance(test_results, (dict, list)):
            return test_results
        
        # Try to parse as JSON first
        if isinstance(test_results, str):
            test_results = test_results.strip()
            if not test_results:
                return {}
            
            # Try JSON parsing
            try:
                import json
                parsed = json.loads(test_results)
                return parsed if isinstance(parsed, (dict, list)) else {"notes": str(parsed)}
            except (json.JSONDecodeError, ValueError):
                # If JSON parsing fails, treat as plain text
                # Convert plain text to a structured format
                lines = [line.strip() for line in test_results.split('\n') if line.strip()]
                
                result = {}
                current_section = "general_notes"
                
                for line in lines:
                    # Check if line contains a colon (key-value pair)
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip().lower().replace(' ', '_').replace('-', '_')
                        value = value.strip()
                        result[key] = value
                    else:
                        # Add to general notes
                        if current_section not in result:
                            result[current_section] = []
                        if isinstance(result[current_section], list):
                            result[current_section].append(line)
                        else:
                            result[current_section] = [result[current_section], line]
                
                # If no structured data found, just store as notes
                if not result:
                    result = {"notes": test_results}
                
                return result
        
        return {}

class MaintenanceRecordQuickForm(forms.ModelForm):
    """Simplified form for quick maintenance record creation"""
    
    class Meta:
        model = MaintenanceRecord
        fields = [
            'circuit_breaker', 'date', 'status', 'priority', 
            'maintenance_carried_out_by', 'remarks'
        ]
        widgets = {
            'circuit_breaker': forms.Select(attrs={'class': 'form-control', 'required': True}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'required': True}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'maintenance_carried_out_by': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Technician name'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Brief description of work performed and any observations'})
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        circuit_breaker_id = kwargs.pop('circuit_breaker_id', None)
        super().__init__(*args, **kwargs)
        
        # Filter to active circuit breakers only
        self.fields['circuit_breaker'].queryset = CircuitBreaker.objects.filter(
            is_active=True
        ).order_by('breaker_number')
        
        # Set circuit breaker if provided
        if circuit_breaker_id and not self.instance.pk:
            try:
                circuit_breaker = CircuitBreaker.objects.get(pk=circuit_breaker_id)
                self.fields['circuit_breaker'].initial = circuit_breaker
            except CircuitBreaker.DoesNotExist:
                pass
    
    def clean_date(self):
        """Validate maintenance date"""
        date = self.cleaned_data.get('date')
        
        if date:
            from django.utils import timezone
            today = timezone.now().date()
            
            # Date cannot be in the future beyond today
            if date > today:
                raise ValidationError("Maintenance date cannot be in the future.")
            
            # Date should not be too old (e.g., more than 2 years ago)
            import datetime
            two_years_ago = today - datetime.timedelta(days=730)
            if date < two_years_ago:
                raise ValidationError("Maintenance date seems too old. Please verify.")
        
        return date

class InsulationResistanceTestForm(forms.ModelForm):
    """Form for individual insulation resistance tests"""
    class Meta:
        model = InsulationResistanceTest
        exclude = ['maintenance_record']
        widgets = {
            'phase': forms.Select(attrs={'class': 'form-control'}),
            'test_type': forms.Select(attrs={'class': 'form-control'}),
            'resistance_value': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'MΩ'
            }),
            'test_voltage': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 1000V, 2500V'
            }),
            'temperature': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'placeholder': '°C'
            }),
            'humidity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 100,
                'placeholder': '%'
            }),
            'result_status': forms.Select(attrs={'class': 'form-control'}),
            'tested_by': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Technician name'
            }),
            'test_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            'comments': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            })
        }

class ContactResistanceTestForm(forms.ModelForm):
    """Form for contact resistance tests"""
    class Meta:
        model = ContactResistanceTest
        exclude = ['maintenance_record']
        widgets = {
            'phase': forms.Select(attrs={'class': 'form-control'}),
            'test_condition': forms.Select(attrs={'class': 'form-control'}),
            'resistance_microohms': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'μΩ'
            }),
            'test_current': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'A'
            }),
            'temperature': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'placeholder': '°C'
            }),
            'result_status': forms.Select(attrs={'class': 'form-control'}),
            'tested_by': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Technician name'
            }),
            'test_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            'comments': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            })
        }

class TimingTestForm(forms.ModelForm):
    """Form for timing tests"""
    class Meta:
        model = TimingTest
        exclude = ['maintenance_record']
        widgets = {
            'phase': forms.Select(attrs={'class': 'form-control'}),
            'operation_type': forms.Select(attrs={'class': 'form-control'}),
            'phu1_time': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'placeholder': 'ms'
            }),
            'phu2_time': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'placeholder': 'ms'
            }),
            'operation_1_close_time': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'placeholder': 'ms'
            }),
            'operation_2_open_time': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'placeholder': 'ms'
            }),
            'operation_3_close_time': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'placeholder': 'ms'
            }),
            'repeat_1st_operation': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'placeholder': 'ms'
            }),
            'repeat_2nd_operation': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'placeholder': 'ms'
            }),
            'result_status': forms.Select(attrs={'class': 'form-control'}),
            'tested_by': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Technician name'
            }),
            'test_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            'comments': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            })
        }

class VacuumBreakerChecksForm(forms.ModelForm):
    """Form for vacuum circuit breaker specific checks"""
    class Meta:
        model = VacuumBreakerChecks
        exclude = ['maintenance_record']
        widgets = {
            'gearing_checked': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'lubrication_checked': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'auxiliary_contacts_checked': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'motor_checked': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'springs_close_open_checked': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'cb_insulators_checked': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'cts_checked': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'porcelain_checked': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'local_remote_operation_checked': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'vacuum_check_performed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'red_phase_ductor': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ductor test result'
            }),
            'yellow_phase_ductor': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ductor test result'
            }),
            'blue_phase_ductor': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ductor test result'
            }),
            'vacuum_level_satisfactory': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'contacts_condition': forms.Select(attrs={'class': 'form-control'}),
            'timing_tests_attached': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'comments': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional comments about vacuum CB maintenance'
            })
        }

class OilBreakerChecksForm(forms.ModelForm):
    """Form for oil circuit breaker specific checks"""
    class Meta:
        model = OilBreakerChecks
        exclude = ['maintenance_record']
        widgets = {
            'oil_level_checked': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'oil_quality_checked': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'oil_leakage_checked': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'oil_condition': forms.Select(attrs={'class': 'form-control'}),
            'oil_dielectric_strength': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'kV'
            }),
            'oil_moisture_content': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'ppm'
            }),
            'oil_acidity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.0001',
                'placeholder': 'mg KOH/g'
            }),
            'contacts_inspection': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'arcing_contacts_condition': forms.Select(attrs={'class': 'form-control'}),
            'tank_condition': forms.Select(attrs={'class': 'form-control'}),
            'gasket_seals_condition': forms.Select(attrs={'class': 'form-control'}),
            'oil_analysis_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'oil_analysis_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'oil_analysis_results': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Oil analysis results'
            }),
            'comments': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional comments about oil CB maintenance'
            })
        }

class TransformerMaintenanceRecordForm(forms.ModelForm):
    """Form for transformer maintenance records"""
    class Meta:
        model = TransformerMaintenanceRecord
        exclude = ['id', 'report_no', 'created_at', 'updated_at']
        widgets = {
            'substation': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Substation name'
            }),
            'transformer_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Transformer number/identifier'
            }),
            'make_manufacturer': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Manufacturer name'
            }),
            'serial_no': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Serial number'
            }),
            'rating_mva': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 25MVA, 100MVA'
            }),
            'voltage_ratio': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 132/11kV, 220/132kV'
            }),
            'year_of_manufacture': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1950,
                'max': 2025,
                'placeholder': 'Year'
            }),
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'required': True
            }),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'maintenance_carried_out_by': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Technician/Team name'
            }),
            'protection_test_carried_out_by': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Protection engineer name'
            }),
            'checked_by': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Checker name'
            }),
            'engineer': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Engineer name'
            }),
            'ops_and_maint_engineer': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'O&M Engineer name'
            }),
            'maintenance_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'protection_test_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'checked_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'engineer_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'ops_maint_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'remarks': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Maintenance remarks and observations'
            })
        }

class AutoRecloseTestForm(forms.ModelForm):
    """Form for auto reclose tests"""
    class Meta:
        model = AutoRecloseTest
        exclude = ['maintenance_record']
        widgets = {
            'reclose_operation_correct': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'lockout_operation_correct': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'result_status': forms.Select(attrs={'class': 'form-control'}),
            'tested_by': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Technician name'
            }),
            'test_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            'comments': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Test comments and observations'
            })
        }

# Inline Formsets for managing related test data
from django.forms import inlineformset_factory

InsulationTestFormSet = inlineformset_factory(
    MaintenanceRecord, 
    InsulationResistanceTest,
    form=InsulationResistanceTestForm,
    extra=3,  # Default to 3 phases
    can_delete=True
)

ContactResistanceTestFormSet = inlineformset_factory(
    MaintenanceRecord,
    ContactResistanceTest,
    form=ContactResistanceTestForm,
    extra=3,  # Default to 3 phases
    can_delete=True
)

TimingTestFormSet = inlineformset_factory(
    MaintenanceRecord,
    TimingTest,
    form=TimingTestForm,
    extra=3,  # Default to 3 phases  
    can_delete=True
)
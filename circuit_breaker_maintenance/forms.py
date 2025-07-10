from django import forms
from .models import CircuitBreaker, MaintenanceRecord

class CircuitBreakerForm(forms.ModelForm):
    class Meta:
        model = CircuitBreaker
        fields = '__all__'
        widgets = {
            'breaker_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., CB-001'}),
            'make_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., ABB, Siemens'}),
            'voltage_capacity': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 33kV, 132kV'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control'}),
            'installation_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'sub_station': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'e.g., Main Substation',
                'list': 'substations'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make required fields more obvious
        required_fields = ['breaker_number', 'make_type', 'voltage_capacity', 'serial_number', 'sub_station']
        for field_name in required_fields:
            self.fields[field_name].widget.attrs.update({'required': True})

class CircuitBreakerFilterForm(forms.Form):
    """Form for filtering circuit breakers"""
    STATUS_CHOICES = [
        ('', 'All Status'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]
    
    substation = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Filter by substation...',
            'list': 'substations'
        })
    )
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search breaker number, make, serial...'
        })
    )
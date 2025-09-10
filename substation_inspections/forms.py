from django import forms
from django.contrib.auth import get_user_model
from .models import (
    Substation, 
    MonthlyInspectionSchedule, 
    MonthlyInspectionReport, 
    InspectionChecklistItem, 
    InspectionItemResponse
)

User = get_user_model()


class SubstationForm(forms.ModelForm):
    """Form for creating and editing substations"""
    
    # Override region field to use ModelChoiceField
    region = forms.ModelChoiceField(
        queryset=None,  # Will be set in __init__
        empty_label="Select a region",
        required=False,
        widget=forms.Select(attrs={
            'class': 'block w-full border border-gray-300 rounded-md px-3 py-2 text-gray-900 focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
        })
    )
    
    class Meta:
        model = Substation
        fields = [
            'substation_code', 'name', 'substation_type', 'voltage_level',
            'location', 'district', 'region',
            'transformers_count', 'circuit_breakers_count', 'switchgear_count',
            'is_active'
        ]
        
        widgets = {
            'substation_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., SUB-001'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Substation Name'
            }),
            'substation_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'voltage_level': forms.Select(attrs={
                'class': 'form-control'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Physical location address'
            }),
            'district': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'District name'
            }),
            'transformers_count': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'circuit_breakers_count': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'switchgear_count': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set region queryset
        from it.users.models import Regions
        self.fields['region'].queryset = Regions.objects.all()
        
        # Make substation_code required for new instances
        if not self.instance.pk:
            self.fields['substation_code'].required = True


class MonthlyInspectionScheduleForm(forms.ModelForm):
    """Form for creating and editing monthly inspection schedules"""
    
    class Meta:
        model = MonthlyInspectionSchedule
        fields = [
            'substation', 'frequency', 'day_of_month', 'assigned_inspector',
            'reminder_days_before', 'escalation_days_after_due', 'is_active'
        ]
        
        widgets = {
            'substation': forms.Select(attrs={
                'class': 'form-control'
            }),
            'frequency': forms.Select(attrs={
                'class': 'form-control'
            }),
            'day_of_month': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '31'
            }),
            'assigned_inspector': forms.Select(attrs={
                'class': 'form-control'
            }),
            'reminder_days_before': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '30'
            }),
            'escalation_days_after_due': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '30'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter active substations
        self.fields['substation'].queryset = Substation.objects.filter(is_active=True)
        # Filter users who can be inspectors (you might want to add a role check here)
        self.fields['assigned_inspector'].queryset = User.objects.filter(is_active=True)


class MonthlyInspectionForm(forms.ModelForm):
    """Form for conducting monthly substation inspections"""
    
    class Meta:
        model = MonthlyInspectionReport
        fields = [
            'substation', 'inspection_date', 'scheduled_date', 'weather_conditions',
            'temperature', 'humidity', 'overall_condition',
            'critical_issues', 'recommendations'
        ]
        
        widgets = {
            'substation': forms.Select(attrs={
                'class': 'form-control'
            }),
            'inspection_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'scheduled_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'weather_conditions': forms.Select(attrs={
                'class': 'form-control'
            }),
            'temperature': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'placeholder': 'Temperature in Celsius'
            }),
            'humidity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100',
                'placeholder': 'Humidity percentage'
            }),
            'overall_condition': forms.Select(attrs={
                'class': 'form-control'
            }),
            'critical_issues': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Critical issues identified...'
            }),
            'recommendations': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Recommendations for improvement...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter active substations
        self.fields['substation'].queryset = Substation.objects.filter(is_active=True)
        
        # Add empty labels for select fields
        self.fields['weather_conditions'].empty_label = "Select weather conditions"
        self.fields['overall_condition'].empty_label = "Select overall condition"
        
        # Set default scheduled_date to inspection_date for new instances
        if not self.instance.pk:
            from datetime import date
            self.fields['scheduled_date'].initial = date.today()
            self.fields['inspection_date'].initial = date.today()


class InspectionChecklistItemForm(forms.ModelForm):
    """Form for creating and editing inspection checklist items"""
    
    class Meta:
        model = InspectionChecklistItem
        fields = [
            'item_code', 'title', 'description', 'equipment_type', 'category', 'severity',
            'is_mandatory', 'is_active', 'reference_standard', 'frequency'
        ]
        
        widgets = {
            'item_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., SAF-001'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Checklist item title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Detailed description of what to check...'
            }),
            'equipment_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'severity': forms.Select(attrs={
                'class': 'form-control'
            }),
            'is_mandatory': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'reference_standard': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., IEEE 141, IEC 61850'
            }),
            'frequency': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., monthly, quarterly'
            })
        }


class InspectionItemResponseForm(forms.ModelForm):
    """Form for individual inspection item responses"""
    
    class Meta:
        model = InspectionItemResponse
        fields = [
            'response', 'observations', 'defect_identified',
            'defect_description', 'defect_severity',
            'corrective_action_required', 'corrective_action_description',
            'target_completion_date'
        ]
        
        widgets = {
            'response': forms.Select(attrs={
                'class': 'form-control',
                'onchange': 'toggleDefectFields(this)'
            }),
            'observations': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Detailed observations...'
            }),
            'defect_identified': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'onchange': 'toggleDefectFields(this)'
            }),
            'defect_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Describe the defect...'
            }),
            'defect_severity': forms.Select(attrs={
                'class': 'form-control'
            }),
            'corrective_action_required': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'onchange': 'toggleCorrectiveActionFields(this)'
            }),
            'corrective_action_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Describe corrective action...'
            }),
            'target_completion_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make response required
        self.fields['response'].required = True


class InspectionReportSearchForm(forms.Form):
    """Form for searching and filtering inspection reports"""
    
    STATUS_CHOICES = [('', 'All Status')] + list(MonthlyInspectionReport.INSPECTION_STATUS_CHOICES)
    COMPLIANCE_CHOICES = [('', 'All Compliance')] + list(MonthlyInspectionReport.COMPLIANCE_STATUS_CHOICES)
    
    substation = forms.ModelChoiceField(
        queryset=Substation.objects.filter(is_active=True),
        required=False,
        empty_label="All Substations",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    compliance_status = forms.ChoiceField(
        choices=COMPLIANCE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    inspector = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        empty_label="All Inspectors",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )


class BulkInspectionAssignmentForm(forms.Form):
    """Form for bulk assignment of inspections to inspectors"""
    
    inspections = forms.ModelMultipleChoiceField(
        queryset=MonthlyInspectionReport.objects.filter(status='scheduled'),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )
    inspector = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Optional notes for the assignment...'
        })
    )

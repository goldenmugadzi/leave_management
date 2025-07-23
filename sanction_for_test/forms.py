from django import forms
from django.contrib.auth.models import User
from .models import SanctionForTestForm, SignatureEntry


class SanctionForTestFormForm(forms.ModelForm):
    """
    ModelForm for creating and editing Sanction For Test forms
    """
    
    class Meta:
        model = SanctionForTestForm
        fields = [
            'status', 'work_to_be_carried_out', 'plant_or_equipment_to_be_tested',
            'points_of_isolation', 'nearest_point_live', 'circuit_main_earth_connected_at',
            'danger_notices', 'caution_notices', 'special_keys', 'other_precaution',
            'exceptions', 'cancellation_reason'
        ]
        
        widgets = {
            'work_to_be_carried_out': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'plant_or_equipment_to_be_tested': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'points_of_isolation': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'other_precaution': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'exceptions': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'cancellation_reason': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'nearest_point_live': forms.TextInput(attrs={'class': 'form-control'}),
            'circuit_main_earth_connected_at': forms.TextInput(attrs={'class': 'form-control'}),
            'danger_notices': forms.TextInput(attrs={'class': 'form-control'}),
            'caution_notices': forms.TextInput(attrs={'class': 'form-control'}),
            'special_keys': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Add helpful placeholders
        self.fields['work_to_be_carried_out'].widget.attrs['placeholder'] = 'Describe the work to be performed...'
        self.fields['plant_or_equipment_to_be_tested'].widget.attrs['placeholder'] = 'List equipment to be tested...'
        self.fields['points_of_isolation'].widget.attrs['placeholder'] = 'Specify isolation points...'
        self.fields['other_precaution'].widget.attrs['placeholder'] = 'Additional safety precautions...'

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        
        # Validation based on status
        if status == 'issued':
            required_fields = ['work_to_be_carried_out', 'plant_or_equipment_to_be_tested']
            for field in required_fields:
                if not cleaned_data.get(field):
                    self.add_error(field, f'This field is required when issuing the form.')
        
        return cleaned_data


class SignatureEntryForm(forms.ModelForm):
    """
    Form for capturing signature entries
    """
    
    class Meta:
        model = SignatureEntry
        fields = ['user', 'name', 'signature', 'date', 'time']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter name'}),
            'signature': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Signature'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Limit user choices to active users
        self.fields['user'].queryset = User.objects.filter(is_active=True).order_by('username')
        self.fields['user'].empty_label = "Select User (Optional)"

    def clean(self):
        cleaned_data = super().clean()
        user = cleaned_data.get('user')
        name = cleaned_data.get('name')
        
        # Ensure either user or name is provided
        if not user and not name:
            raise forms.ValidationError('Either select a user or enter a name.')
        
        # Auto-fill name from user if user is selected but name is empty
        if user and not name:
            cleaned_data['name'] = f"{user.first_name} {user.last_name}".strip() or user.username
        
        return cleaned_data


class QuickActionForm(forms.Form):
    """
    Form for quick actions on Sanction For Test forms
    """
    ACTION_CHOICES = [
        ('issue', 'Issue Form'),
        ('receive', 'Receive Form'),
        ('clear', 'Clear Form'),
        ('cancel', 'Cancel Form'),
        ('complete', 'Complete Form'),
    ]
    
    action = forms.ChoiceField(choices=ACTION_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))
    comment = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Add a comment...'}),
        required=False
    )
    signature_name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your name'}),
        required=False
    )

    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        
        # Require signature name for certain actions
        if action in ['issue', 'receive', 'clear', 'cancel'] and not cleaned_data.get('signature_name'):
            self.add_error('signature_name', 'Signature name is required for this action.')
        
        return cleaned_data

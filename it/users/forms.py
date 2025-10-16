# users/forms.py

from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.utils import timezone
from datetime import timedelta
from .models import Responsibilities, RoleDelegation, UserProfile, Roles, Application

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        fields = UserCreationForm.Meta.fields + ("email",)
    
    def __init__(self, *args, **kwargs):
        super(UserCreationForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['email'].widget.attrs.update({'class': 'form-control'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})

class ResponsibilitiesForm(forms.ModelForm):
    class Meta:
        model = Responsibilities
        fields = "__all__"
        exclude = ['user']
        # widgets = {
        #     'role': forms.Select(attrs={'class': 'form-control select2'}),
        #     'cost_centers': forms.Select(attrs={'class': 'form-control select2','multiple': 'multiple'}),
        # }
    def __init__(self, *args, **kwargs):
        roles_queryset = kwargs.pop('roles_queryset', None)
        cost_centers_queryset = kwargs.pop('cost_centers_queryset', None)
        super().__init__(*args, **kwargs)

        if roles_queryset is not None:
            self.fields['role'].queryset = roles_queryset
        if cost_centers_queryset is not None:
            self.fields['cost_centers'].queryset = cost_centers_queryset

        for field_name, field in self.fields.items():
            if(field_name == 'cost_centers'):
                field.widget.attrs.update({
                 'multiple': 'multiple',   'class': "block w-full hidden rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",
                })
            else:
                field.widget.attrs.update({
                'class': "imline m-3   px-2 form-control select2 text-center rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",
            })


class RoleDelegationForm(forms.ModelForm):
    """Form for creating role delegations"""
    
    class Meta:
        model = RoleDelegation
        fields = ['delegatee', 'start_date', 'end_date', 'reason']
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'reason': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        self.delegator = kwargs.pop('delegator', None)
        self.current_user = kwargs.pop('current_user', None)
        self.allow_delegator_selection = kwargs.pop('allow_delegator_selection', False)
        super().__init__(*args, **kwargs)
        
        # Add delegator field if allowed
        if self.allow_delegator_selection and self.current_user and self.current_user.can_approve_delegations():
            self.fields['delegator'] = forms.ModelChoiceField(
                queryset=UserProfile.objects.filter(roles__isnull=False).distinct(),
                empty_label="Select delegator",
                help_text="Select the user whose roles will be delegated"
            )
            self.fields['delegator'].widget.attrs.update({
                'class': 'form-control select2'
            })
            # Reorder fields to put delegator first
            field_order = ['delegator', 'delegatee', 'start_date', 'end_date', 'reason']
            self.fields = {k: self.fields[k] for k in field_order if k in self.fields}
        
        # Set default start date to now
        if not self.instance.pk:
            self.fields['start_date'].initial = timezone.now()
            # Set default end date to 7 days from now
            self.fields['end_date'].initial = timezone.now() + timedelta(days=7)
        
        # Customize querysets
        if self.delegator:
            # Only show users from the same region/cost center
            self.fields['delegatee'].queryset = UserProfile.objects.filter(
                region=self.delegator.region
            ).exclude(id=self.delegator.id)
        
        # Add CSS classes
        for field_name, field in self.fields.items():
            if field_name in ['delegatee', 'delegator']:
                field.widget.attrs.update({
                    'class': 'form-control select2'
                })
            elif field_name == 'reason':
                field.widget.attrs.update({
                    'class': 'form-control',
                    'placeholder': 'Enter reason for delegation (e.g., leave, training, etc.)'
                })
            else:
                field.widget.attrs.update({
                    'class': 'form-control'
                })
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        delegatee = cleaned_data.get('delegatee')
        
        # Validate date range
        if start_date and end_date:
            if start_date >= end_date:
                raise forms.ValidationError("End date must be after start date.")
            
            if start_date < timezone.now():
                raise forms.ValidationError("Start date cannot be in the past.")
            
            # Check if delegation period is too long (max 90 days)
            if (end_date - start_date).days > 90:
                raise forms.ValidationError("Delegation period cannot exceed 90 days.")
        
        # Validate delegatee
        if delegatee and self.delegator:
            if delegatee == self.delegator:
                raise forms.ValidationError("You cannot delegate roles to yourself.")
            
            # Check if delegatee is in the same region
            if delegatee.region != self.delegator.region:
                raise forms.ValidationError("You can only delegate to users in the same region.")
        
        return cleaned_data


class DelegationApprovalForm(forms.Form):
    """Form for approving or rejecting delegations"""
    
    ACTION_CHOICES = [
        ('APPROVE', 'Approve'),
        ('REJECT', 'Reject'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    comments = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        help_text="Add comments for approval or rejection reason"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['comments'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter comments...'
        })


class DelegationSearchForm(forms.Form):
    """Form for searching and filtering delegations"""
    
    STATUS_CHOICES = [
        ('', 'All Statuses'),
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('ACTIVE', 'Active'),
        ('EXPIRED', 'Expired'),
        ('CANCELLED', 'Cancelled'),
        ('REJECTED', 'Rejected'),
    ]
    
    TYPE_CHOICES = [
        ('', 'All Types'),
        ('DELEGATED', 'Delegated by Me'),
        ('RECEIVED', 'Received by Me'),
        ('APPROVED', 'Approved by Me'),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    delegation_type = forms.ChoiceField(
        choices=TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by username, reason, or role...'
        })
    )
   
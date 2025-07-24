from django import forms
from django.contrib.auth.models import User
from .models import (
    SanctionForTestForm, SanctionFormComment, 
    SanctionFormAttachment
)
from it.users.models import UserProfile


class SanctionForTestFormForm(forms.ModelForm):
    """
    ModelForm for creating and editing Sanction For Test forms
    """
    
    class Meta:
        model = SanctionForTestForm
        fields = [
            'priority', 'risk_level', 'region', 'district', 'section', 'depot', 'cost_center',
            'work_to_be_carried_out', 'plant_or_equipment_to_be_tested',
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
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'risk_level': forms.Select(attrs={'class': 'form-control'}),
            'region': forms.Select(attrs={'class': 'form-control'}),
            'district': forms.Select(attrs={'class': 'form-control'}),
            'section': forms.Select(attrs={'class': 'form-control'}),
            'depot': forms.Select(attrs={'class': 'form-control'}),
            'cost_center': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Pre-populate fields from user profile if user is provided
        if self.user and not self.instance.pk:
            if hasattr(self.user, 'userprofile'):
                profile = self.user.userprofile
                if profile.region:
                    self.fields['region'].initial = profile.region
                if profile.district:
                    self.fields['district'].initial = profile.district
                if profile.section:
                    self.fields['section'].initial = profile.section
                if profile.depot:
                    self.fields['depot'].initial = profile.depot
                if profile.cost_center:
                    self.fields['cost_center'].initial = profile.cost_center
        
        # Add helpful placeholders
        self.fields['work_to_be_carried_out'].widget.attrs['placeholder'] = 'Describe the work to be performed...'
        self.fields['plant_or_equipment_to_be_tested'].widget.attrs['placeholder'] = 'List equipment to be tested...'
        self.fields['points_of_isolation'].widget.attrs['placeholder'] = 'Specify isolation points...'
        self.fields['other_precaution'].widget.attrs['placeholder'] = 'Additional safety precautions...'

    def clean(self):
        cleaned_data = super().clean()
        
        # Basic validation for required technical fields
        required_fields = ['work_to_be_carried_out', 'plant_or_equipment_to_be_tested']
        for field in required_fields:
            if not cleaned_data.get(field):
                self.add_error(field, f'This field is required.')
        
        return cleaned_data


class SanctionFormCommentForm(forms.ModelForm):
    """
    Form for adding comments to sanction forms
    """
    
    class Meta:
        model = SanctionFormComment
        fields = ['comment', 'is_private']
        widgets = {
            'comment': forms.Textarea(attrs={
                'rows': 4, 
                'class': 'form-control', 
                'placeholder': 'Add your comment here...'
            }),
            'is_private': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class SanctionFormAttachmentForm(forms.ModelForm):
    """
    Form for uploading attachments to sanction forms
    """
    
    class Meta:
        model = SanctionFormAttachment
        fields = ['file', 'attachment_type', 'description']
        widgets = {
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'attachment_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Brief description of the attachment'
            }),
        }


class SanctionFormStatusUpdateForm(forms.Form):
    """
    Form for updating the status of a sanction form
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('awaiting_approval', 'Awaiting Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    comment = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Optional comment about the status change...'}),
        required=False
    )

    def __init__(self, *args, **kwargs):
        current_status = kwargs.pop('current_status', None)
        super().__init__(*args, **kwargs)
        
        if current_status:
            self.fields['status'].initial = current_status
            self.fields['status'].help_text = f"Current status: {current_status}"


class ApprovalActionForm(forms.Form):
    """
    Form for approval actions on sanction forms
    """
    ACTION_CHOICES = [
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('request_changes', 'Request Changes'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    comment = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Add your approval comment...'}),
        required=True,
        help_text="Please provide a reason for your decision"
    )

    def clean_comment(self):
        comment = self.cleaned_data.get('comment')
        if not comment or len(comment.strip()) < 10:
            raise forms.ValidationError('Please provide a meaningful comment (at least 10 characters).')
        return comment.strip()

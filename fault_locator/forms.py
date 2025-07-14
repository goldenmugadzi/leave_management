from django import forms
from .models import Fault, FaultLocatorDevice, FaultLocatorTeam, FaultLocatorDeviceAssignment, FaultAssignment, TeamDeployment, FaultLocatorRole
from it.users.models import UserProfile, Depots
from django_select2.forms import Select2MultipleWidget

class FaultForm(forms.ModelForm):
    class Meta:
        model = Fault
        fields = ['description', 'depot']

class FaultLocatorDeviceForm(forms.ModelForm):
    class Meta:
        model = FaultLocatorDevice
        fields = ['serial_number', 'description']

class FaultLocatorTeamForm(forms.ModelForm):
    class Meta:
        model = FaultLocatorTeam
        fields = ['name', 'members']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full p-3 sm:p-4 border-2 border-nepal-200 rounded-lg sm:rounded-xl bg-white/80 backdrop-blur-sm text-nepal-800 text-sm sm:text-base focus:border-gulf-blue-400 focus:ring-gulf-blue-400 focus:ring-opacity-50 transition-all duration-300',
                'placeholder': 'e.g., Alpha Team, North District Crew'
            }),
            'members': Select2MultipleWidget(attrs={
                'class': 'w-full',
                'data-placeholder': 'Select team members',
                'data-theme': 'bootstrap-5'
            }),
        }

class FaultLocatorTeamNameForm(forms.ModelForm):
    class Meta:
        model = FaultLocatorTeam
        fields = ['name']

class AddTeamMemberForm(forms.Form):
    member = forms.ModelChoiceField(
        queryset=UserProfile.objects.all(),
        label="Add Member"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply ACE-style classes
        self.fields['member'].widget.attrs.update({
            'class': "select2 block w-full rounded-md border-0 py-1.5 text-gray-900 "
                     "shadow-sm ring-1 ring-inset ring-gray-300 "
                     "placeholder:text-gray-400 focus:ring-2 focus:ring-inset "
                     "focus:ring-indigo-600 sm:text-sm sm:leading-6"
        })
        self.fields['member'].label_attrs = {'class': 'block text-sm font-medium leading-6 text-gray-900'}

class AssignDeviceToTeamForm(forms.ModelForm):
    class Meta:
        model = FaultLocatorDeviceAssignment
        fields = ['device', 'team']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show devices not already assigned
        assigned_devices = FaultLocatorDeviceAssignment.objects.values_list('device_id', flat=True)
        self.fields['device'].queryset = FaultLocatorDevice.objects.exclude(id__in=assigned_devices)

    def clean_device(self):
        device = self.cleaned_data['device']
        if FaultLocatorDeviceAssignment.objects.filter(device=device).exists():
            raise forms.ValidationError("This device is already assigned to a team.")
        return device

class AssignFaultForm(forms.ModelForm):
    class Meta:
        model = FaultAssignment
        fields = ['fault', 'team']  # Remove 'device' from the form

class TeamDeploymentForm(forms.ModelForm):
    class Meta:
        model = TeamDeployment
        fields = ['team', 'depot', 'deployment_notes']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show teams that have devices assigned and are not currently deployed
        teams_with_devices = FaultLocatorDeviceAssignment.objects.values_list('team_id', flat=True)
        self.fields['team'].queryset = FaultLocatorTeam.objects.filter(
            id__in=teams_with_devices,
            current_depot__isnull=True
        )
        
        self.fields['team'].widget.attrs.update({
            'class': 'form-select'
        })
        self.fields['depot'].widget.attrs.update({
            'class': 'form-select'
        })
        self.fields['deployment_notes'].widget.attrs.update({
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter deployment instructions...'
        })
        self.fields['deployment_notes'].label = 'Deployment Notes'

class SeniorForepersonDeviceAssignmentForm(forms.ModelForm):
    class Meta:
        model = FaultLocatorDeviceAssignment
        fields = ['device', 'team']
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # This will now be a UserProfile instance
        super().__init__(*args, **kwargs)
        
        # Only show unassigned devices
        assigned_devices = FaultLocatorDeviceAssignment.objects.values_list('device_id', flat=True)
        self.fields['device'].queryset = FaultLocatorDevice.objects.exclude(id__in=assigned_devices)
        
        # Show all teams for senior foreperson
        if user and self.is_senior_foreperson(user):
            self.fields['team'].queryset = FaultLocatorTeam.objects.all()
        
        self.fields['device'].widget.attrs.update({
            'class': 'form-select'
        })
        self.fields['team'].widget.attrs.update({
            'class': 'form-select'
        })
    
    def is_senior_foreperson(self, user_profile):
        """Check if user profile has senior foreperson designation"""
        if not user_profile or not hasattr(user_profile, 'designation') or not user_profile.designation:
            return False
        
        designation_desc = user_profile.designation.description.lower()
        return 'senior' in designation_desc and 'foreperson' in designation_desc

class FaultPriorityForm(forms.ModelForm):
    class Meta:
        model = Fault
        fields = ['priority']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['priority'].widget.attrs.update({
            'class': 'form-select'
        })

class FaultLocatorRoleForm(forms.ModelForm):
    """Form for assigning fault locator roles to users"""
    class Meta:
        model = FaultLocatorRole
        fields = ['user', 'role', 'depot']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter active users
        self.fields['user'].queryset = UserProfile.objects.filter(is_active=True).order_by('last_name', 'first_name')
        
        # Add CSS classes
        self.fields['user'].widget.attrs.update({
            'class': 'form-select'
        })
        self.fields['role'].widget.attrs.update({
            'class': 'form-select'
        })
        self.fields['depot'].widget.attrs.update({
            'class': 'form-select'
        })
        
        # Make depot optional for certain roles
        self.fields['depot'].required = False
        
        # Add help text
        self.fields['depot'].help_text = "Required only for depot foreperson role"
    
    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        depot = cleaned_data.get('depot')
        
        # Depot is required for depot foreperson
        if role == 'depot_foreperson' and not depot:
            raise forms.ValidationError("Depot is required for depot foreperson role")
        
        # Depot should not be set for senior foreman
        if role == 'senior_foreman' and depot:
            cleaned_data['depot'] = None
        
        return cleaned_data

class TeamLeaderAssignmentForm(forms.ModelForm):
    """Form for assigning team leaders"""
    team_leader = forms.ModelChoiceField(
        queryset=UserProfile.objects.filter(is_active=True),
        required=False,
        label="Team Leader",
        help_text="Select a user to be the team leader"
    )
    
    class Meta:
        model = FaultLocatorTeam
        fields = ['team_leader']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['team_leader'].widget.attrs.update({
            'class': 'form-select'
        })

class FaultStatusUpdateForm(forms.ModelForm):
    """Form for team leaders to update fault status"""
    class Meta:
        model = Fault
        fields = ['status', 'team_leader_notes', 'location_details']
    
    def __init__(self, *args, **kwargs):
        user_role = kwargs.pop('user_role', None)
        super().__init__(*args, **kwargs)
        
        # Limit status choices based on user role
        if user_role == 'team_leader':
            self.fields['status'].choices = [
                ('assigned', 'In Progress'),
                ('located', 'Fault Located'),
            ]
        elif user_role == 'depot_foreperson':
            self.fields['status'].choices = [
                ('assigned', 'In Progress'),
                ('located', 'Fault Located'),
                ('verified', 'Verified'),
                ('closed', 'Closed'),
            ]
        
        # Add CSS classes and placeholders
        self.fields['status'].widget.attrs.update({
            'class': 'form-select'
        })
        self.fields['team_leader_notes'].widget.attrs.update({
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Add notes about fault location work...'
        })
        self.fields['location_details'].widget.attrs.update({
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Provide detailed location information...'
        })

class QuickFaultReportForm(forms.ModelForm):
    """Simplified form for quick fault reporting"""
    class Meta:
        model = Fault
        fields = ['description', 'depot', 'priority']
    
    def __init__(self, *args, **kwargs):
        user_depot = kwargs.pop('user_depot', None)
        super().__init__(*args, **kwargs)
        
        # If user has a specific depot, pre-select it
        if user_depot:
            self.fields['depot'].initial = user_depot
            self.fields['depot'].queryset = Depots.objects.filter(id=user_depot.id)
        
        # Add CSS classes
        self.fields['description'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Describe the fault...',
            'rows': 3
        })
        self.fields['depot'].widget.attrs.update({
            'class': 'form-select'
        })
        self.fields['priority'].widget.attrs.update({
            'class': 'form-select'
        })
from django import forms
from .models import Fault, FaultLocatorDevice, FaultLocatorTeam, FaultLocatorDeviceAssignment, FaultAssignment, TeamDeployment, FaultLocatorRole
from it.users.models import UserProfile, Depots
from django_select2.forms import Select2MultipleWidget

class FaultForm(forms.ModelForm):
    class Meta:
        model = Fault
        fields = ['description', 'depot']
        widgets = {
            'description': forms.Textarea(attrs={
                'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6',
                'rows': 3,
                'placeholder': 'Describe the fault in detail...'
            }),
            'depot': forms.Select(attrs={
                'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6',
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure depot field has choices
        self.fields['depot'].queryset = Depots.objects.all().order_by('depot')
        self.fields['depot'].empty_label = "Select a depot..."

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
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all duration-200',
                'placeholder': 'e.g., Alpha Team, North District Crew'
            }),
            'members': Select2MultipleWidget(attrs={
                'class': 'w-full',
                'data-placeholder': 'Search and select team members from your region',
                'data-theme': 'bootstrap-5',
                'data-minimum-input-length': '2'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        user_region = kwargs.pop('user_region', None)
        super().__init__(*args, **kwargs)
        
        # Filter members by user's region
        if user_region:
            self.fields['members'].queryset = UserProfile.objects.filter(
                region=user_region,
                is_active=True
            ).exclude(
                username__in=['admin', 'superuser']
            ).order_by('last_name', 'first_name')
        else:
            # Fallback to all active users if no region specified
            self.fields['members'].queryset = UserProfile.objects.filter(
                is_active=True
            ).exclude(
                username__in=['admin', 'superuser']
            ).order_by('last_name', 'first_name')

class FaultLocatorTeamNameForm(forms.ModelForm):
    class Meta:
        model = FaultLocatorTeam
        fields = ['name']

class AddTeamMemberForm(forms.Form):
    member = forms.ModelChoiceField(
        queryset=UserProfile.objects.none(),  # Will be set in __init__
        label="Add Member",
        widget=forms.Select(attrs={
            'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all duration-200',
            'data-placeholder': 'Search and select a member from your region...'
        })
    )

    def __init__(self, *args, **kwargs):
        user_region = kwargs.pop('user_region', None)
        team = kwargs.pop('team', None)
        super().__init__(*args, **kwargs)
        
        # Base queryset - active users from the same region
        base_queryset = UserProfile.objects.filter(is_active=True).exclude(
            username__in=['admin', 'superuser']
        )
        
        # Filter by region if provided
        if user_region:
            base_queryset = base_queryset.filter(region=user_region)
        
        # Exclude current team members if team is provided
        if team:
            base_queryset = base_queryset.exclude(
                id__in=team.members.values_list('id', flat=True)
            )
        
        # Order by name for better UX
        self.fields['member'].queryset = base_queryset.order_by('last_name', 'first_name')
        
        # Set empty label
        self.fields['member'].empty_label = "Select a member to add..."

class AssignDeviceToTeamForm(forms.ModelForm):
    class Meta:
        model = FaultLocatorDeviceAssignment
        fields = ['device', 'team']

    def __init__(self, *args, **kwargs):
        user_region = kwargs.pop('user_region', None)
        super().__init__(*args, **kwargs)
        
        # Only show devices not already assigned
        assigned_devices = FaultLocatorDeviceAssignment.objects.values_list('device_id', flat=True)
        device_queryset = FaultLocatorDevice.objects.exclude(id__in=assigned_devices)
        
        # Devices are equipment that can be used anywhere, so no regional filtering needed
        # All available devices can be assigned to teams
        
        self.fields['device'].queryset = device_queryset
        
        # Apply regional filtering for teams if user_region is provided
        if user_region:
            from it.users.models import UserProfile
            users_in_region = UserProfile.objects.filter(
                region=user_region,
                is_active=True
            ).values_list('id', flat=True)
            
            self.fields['team'].queryset = FaultLocatorTeam.objects.filter(
                members__in=users_in_region
            ).distinct()
        else:
            # Show all teams if no region specified
            self.fields['team'].queryset = FaultLocatorTeam.objects.all()

    def clean_device(self):
        device = self.cleaned_data['device']
        if FaultLocatorDeviceAssignment.objects.filter(device=device).exists():
            raise forms.ValidationError("This device is already assigned to a team.")
        return device

class AssignFaultForm(forms.ModelForm):
    class Meta:
        model = FaultAssignment
        fields = ['fault', 'team']  # Remove 'device' from the form
    
    def __init__(self, *args, **kwargs):
        user_region = kwargs.pop('user_region', None)
        super().__init__(*args, **kwargs)
        
        # Apply regional filtering for teams if user_region is provided
        if user_region:
            from it.users.models import UserProfile
            users_in_region = UserProfile.objects.filter(
                region=user_region,
                is_active=True
            ).values_list('user_id', flat=True)
            
            self.fields['team'].queryset = FaultLocatorTeam.objects.filter(
                members__in=users_in_region
            ).distinct()
        
        # Apply regional filtering for faults if user_region is provided
        if user_region:
            self.fields['fault'].queryset = self.fields['fault'].queryset.filter(
                depot__region=user_region
            )

class TeamDeploymentForm(forms.ModelForm):
    class Meta:
        model = TeamDeployment
        fields = ['team', 'depot', 'deployment_notes']
    
    def __init__(self, *args, **kwargs):
        user_region = kwargs.pop('user_region', None)
        super().__init__(*args, **kwargs)
        
        # Only show teams that have devices assigned and are not currently deployed
        teams_with_devices = FaultLocatorDeviceAssignment.objects.values_list('team_id', flat=True)
        team_queryset = FaultLocatorTeam.objects.filter(
            id__in=teams_with_devices,
            current_depot__isnull=True
        )
        
        # Apply regional filtering if user_region is provided
        if user_region:
            # Filter teams by members from the same region
            from it.users.models import UserProfile
            users_in_region = UserProfile.objects.filter(
                region=user_region,
                is_active=True
            ).values_list('user_id', flat=True)
            
            team_queryset = team_queryset.filter(
                members__in=users_in_region
            ).distinct()
        
        self.fields['team'].queryset = team_queryset
        
        # Filter depots by region if user_region is provided
        if user_region:
            self.fields['depot'].queryset = self.fields['depot'].queryset.filter(
                region=user_region
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
        device_queryset = FaultLocatorDevice.objects.exclude(id__in=assigned_devices)
        
        # Devices are equipment that can be used anywhere, so no regional filtering needed
        # All available devices can be assigned to teams
        
        self.fields['device'].queryset = device_queryset
        
        # Show teams based on user permissions and region
        if user and self.is_senior_foreperson(user):
            team_queryset = FaultLocatorTeam.objects.all()
            
            # Apply regional filtering for teams if user has a region
            if user.region:
                from it.users.models import UserProfile
                users_in_region = UserProfile.objects.filter(
                    region=user.region,
                    is_active=True
                ).values_list('id', flat=True)
                
                team_queryset = team_queryset.filter(
                    members__in=users_in_region
                ).distinct()
            
            self.fields['team'].queryset = team_queryset
        else:
            # For non-senior forepersons, show all teams (can be restricted later if needed)
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
        user_region = kwargs.pop('user_region', None)
        user_depot = kwargs.pop('user_depot', None)
        super().__init__(*args, **kwargs)
        
        # Apply regional filtering for depots
        depot_queryset = Depots.objects.all()
        if user_region:
            depot_queryset = depot_queryset.filter(region=user_region)
        
        # If user has a specific depot, pre-select it
        if user_depot:
            self.fields['depot'].initial = user_depot
            # For non-senior users, restrict to their depot only
            if not user_region:  # If no region filtering, means it's restricted to user's depot
                depot_queryset = depot_queryset.filter(id=user_depot.id)
        
        self.fields['depot'].queryset = depot_queryset.order_by('depot')
        
        # Use Select2 widget for searchable depot selection
        self.fields['depot'].widget = forms.Select(attrs={
            'class': 'form-select depot-select',
            'data-placeholder': 'Search and select depot...',
            'data-allow-clear': 'true'
        })
        
        # Add CSS classes
        self.fields['description'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Describe the fault...',
            'rows': 3
        })
        self.fields['priority'].widget.attrs.update({
            'class': 'form-select'
        })
from django import forms
from .models import Fault, FaultLocatorDevice, FaultLocatorTeam, FaultLocatorDeviceAssignment, FaultAssignment, TeamDeployment, FaultLocatorRole
from .models import CraneTruck, CraneRequest, CraneJobReport, Vehicle
from it.users.models import UserProfile, Depots
from django_select2.forms import Select2MultipleWidget

class FaultForm(forms.ModelForm):
    class Meta:
        model = Fault
        fields = ['description', 'depot', 'vvip', 'voltage', 'backfeed', 'clients_affected']
        widgets = {
            'description': forms.Textarea(attrs={
                'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6',
                'rows': 3,
                'placeholder': 'Describe the fault in detail...'
            }),
            'depot': forms.Select(attrs={
                'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6',
            }),
            'vvip': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-red-600 shadow-sm focus:ring-red-500',
            }),
            'voltage': forms.Select(attrs={
                'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6',
            }),
            'backfeed': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-indigo-600 shadow-sm focus:ring-indigo-500',
            }),
            'clients_affected': forms.NumberInput(attrs={
                'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6',
                'placeholder': 'Number of clients affected',
                'min': '0'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure depot field has choices
        self.fields['depot'].queryset = Depots.objects.all().order_by('depot')
        self.fields['depot'].empty_label = "Select a depot..."
        
        # Ensure voltage choices are available (defensive in case of widget overrides)
        try:
            self.fields['voltage'].choices = [('', 'Select voltage level...')] + list(Fault.VOLTAGE_CHOICES)
        except Exception:
            # If for some reason voltage field isn't present, skip silently
            pass

        # Add field labels and help text
        self.fields['vvip'].label = 'VVIP Fault'
        self.fields['vvip'].help_text = 'Check if this is a VVIP fault (takes absolute priority over all other faults)'
        self.fields['voltage'].label = 'Voltage Level'
        self.fields['voltage'].help_text = 'Select the voltage level for this fault'
        self.fields['backfeed'].label = 'Backfeed Available'
        self.fields['backfeed'].help_text = 'Check if backfeed is available for this fault'
        self.fields['clients_affected'].label = 'Clients Affected'
        self.fields['clients_affected'].help_text = 'Number of clients affected by this fault'

class FaultLocatorDeviceForm(forms.ModelForm):
    class Meta:
        model = FaultLocatorDevice
        fields = ['serial_number', 'description']

class FaultLocatorTeamForm(forms.ModelForm):
    class Meta:
        model = FaultLocatorTeam
        fields = ['name', 'team_leader', 'members']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all duration-200',
                'placeholder': 'e.g., Alpha Team, North District Crew'
            }),
            'team_leader': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all duration-200',
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
        
        # Populate team_leader choices
        if self.instance and self.instance.pk:
            self.fields['team_leader'].queryset = self.instance.members.all()
        else:
            self.fields['team_leader'].queryset = UserProfile.objects.none()

        # Filter members by user's region and exclude those who can't be added to teams
        if user_region:
            # Import here to avoid circular imports
            from .views import is_depot_foreperson, is_senior_foreman
            
            # Get base queryset of active users in the region
            base_queryset = UserProfile.objects.filter(
                region=user_region,
                is_active=True
            ).exclude(
                username__in=['admin', 'superuser']
            )
            
            # Filter out users who are already in teams or are forepersons
            valid_members = []
            for user in base_queryset:
                # Check if user is already in a team
                if self.instance and self.instance.pk:
                    if user.fault_locator_teams.exclude(pk=self.instance.pk).exists():
                        continue
                elif user.fault_locator_teams.exists():
                    continue
                
                # Check if user is a team leader
                if self.instance and self.instance.pk:
                    if FaultLocatorTeam.objects.filter(team_leader=user).exclude(pk=self.instance.pk).exists():
                        continue
                elif FaultLocatorTeam.objects.filter(team_leader=user).exists():
                    continue
                
                # Check if user is a depot foreperson or senior foreperson
                if is_depot_foreperson(user) or is_senior_foreman(user):
                    continue
                
                valid_members.append(user.id)
            
            self.fields['members'].queryset = base_queryset.filter(
                id__in=valid_members
            ).order_by('last_name', 'first_name')
        else:
            # Fallback to all active users if no region specified
            # Import here to avoid circular imports
            from .views import is_depot_foreperson, is_senior_foreman
            
            base_queryset = UserProfile.objects.filter(
                is_active=True
            ).exclude(
                username__in=['admin', 'superuser']
            )
            
            # Filter out users who are already in teams or are forepersons
            valid_members = []
            for user in base_queryset:
                # Check if user is already in a team
                if self.instance and self.instance.pk:
                    if user.fault_locator_teams.exclude(pk=self.instance.pk).exists():
                        continue
                elif user.fault_locator_teams.exists():
                    continue
                
                # Check if user is a team leader
                if self.instance and self.instance.pk:
                    if FaultLocatorTeam.objects.filter(team_leader=user).exclude(pk=self.instance.pk).exists():
                        continue
                elif FaultLocatorTeam.objects.filter(team_leader=user).exists():
                    continue
                
                # Check if user is a depot foreperson or senior foreperson
                if is_depot_foreperson(user) or is_senior_foreman(user):
                    continue
                
                valid_members.append(user.id)
            
            self.fields['members'].queryset = base_queryset.filter(
                id__in=valid_members
            ).order_by('last_name', 'first_name')
        
        self.fields['team_leader'].required = False
    
    def clean_members(self):
        """Validate that selected members can be added to teams"""
        members = self.cleaned_data.get('members')
        if not members:
            return members
        
        # Import here to avoid circular imports
        from .views import can_user_be_added_to_team
        
        errors = []
        for member in members:
            can_add, reason = can_user_be_added_to_team(member)
            if not can_add:
                errors.append(f"{member.get_full_name()}: {reason}")
        
        if errors:
            raise forms.ValidationError("Cannot add the following members: " + "; ".join(errors))
        
        return members

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
        
        # Filter out users who can't be added to teams
        # Import here to avoid circular imports
        from .views import is_depot_foreperson, is_senior_foreman
        
        valid_members = []
        for user in base_queryset:
            # Check if user is already in another team
            if user.fault_locator_teams.exists():
                continue
            
            # Check if user is a team leader of another team
            if FaultLocatorTeam.objects.filter(team_leader=user).exists():
                continue
            
            # Check if user is a depot foreperson or senior foreperson
            if is_depot_foreperson(user) or is_senior_foreman(user):
                continue
            
            valid_members.append(user.id)
        
        # Order by name for better UX
        self.fields['member'].queryset = base_queryset.filter(
            id__in=valid_members
        ).order_by('last_name', 'first_name')
        
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
        # Support independent filtering for teams vs depots
        user_region = kwargs.pop('user_region', None)  # Backward-compat: used if specific regions not provided
        team_region = kwargs.pop('team_region', None)
        depot_region = kwargs.pop('depot_region', None)
        # If only user_region provided, apply to both (legacy behavior)
        if user_region and team_region is None and depot_region is None:
            team_region = user_region
            depot_region = user_region
        super().__init__(*args, **kwargs)
        
        # Only show teams that have devices assigned and are not currently deployed
        teams_with_devices = FaultLocatorDeviceAssignment.objects.select_related('device').filter(
            device__status__in=['available', 'assigned']  # Only working devices
        ).values_list('team_id', flat=True)
        team_queryset = FaultLocatorTeam.objects.filter(
            id__in=teams_with_devices,
            current_depot__isnull=True
        )
        
        # Apply regional filtering for teams if team_region is provided
        if team_region:
            # Filter teams by members from the same region
            from it.users.models import UserProfile
            users_in_region = UserProfile.objects.filter(
                region=team_region,
                is_active=True
            ).values_list('id', flat=True)
            
            team_queryset = team_queryset.filter(
                members__in=users_in_region
            ).distinct()
        
        self.fields['team'].queryset = team_queryset
        
        # Filter depots by region if depot_region is provided
        if depot_region:
            self.fields['depot'].queryset = self.fields['depot'].queryset.filter(
                region=depot_region
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
            # Senior foremen can assign devices to any team (no regional restriction)
            self.fields['team'].queryset = FaultLocatorTeam.objects.all()
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

class CraneTruckForm(forms.ModelForm):
    class Meta:
        model = CraneTruck
        fields = ['fleet_number', 'number_plate', 'mileage_km', 'status', 'operator']
        widgets = {
            'fleet_number': forms.TextInput(attrs={'class': 'form-control'}),
            'number_plate': forms.TextInput(attrs={'class': 'form-control'}),
            'mileage_km': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            # add select2 for searching operators
            'operator': forms.Select(attrs={'class': 'form-select select2', 'data-placeholder': 'Search operator...'}),
        }

    def __init__(self, *args, **kwargs):
        # Accept user_region to scope operator options
        user_region = kwargs.pop('user_region', None)
        super().__init__(*args, **kwargs)
        # Filter operators by region when provided; fall back to all active users
        # Start with users who have the Crane Operator role in central roles
        try:
            from .central_roles import FaultLocatorRoleManager
            qs = FaultLocatorRoleManager.get_users_with_role(FaultLocatorRoleManager.CRANE_OPERATOR)
            qs = qs.filter(is_active=True)
        except Exception:
            # Fallback to all active users if central roles unavailable
            qs = UserProfile.objects.filter(is_active=True)
        if user_region:
            qs = qs.filter(region=user_region)
        self.fields['operator'].queryset = qs.order_by('last_name', 'first_name')
        # Ensure widget keeps select2 class if replaced elsewhere
        self.fields['operator'].widget.attrs.setdefault('class', 'form-select select2')
        self.fields['operator'].empty_label = '---------'

        # Make identifiers read-only when editing existing instance
        if self.instance and self.instance.pk:
            self.fields['fleet_number'].disabled = True
            self.fields['number_plate'].disabled = True

    def clean(self):
        """Extra guard to prevent duplicates and changes of identifiers."""
        cleaned = super().clean()
        fleet_number = cleaned.get('fleet_number')
        number_plate = cleaned.get('number_plate')
        # If creating new, enforce uniqueness explicitly for friendlier error
        if not (self.instance and self.instance.pk):
            if fleet_number and CraneTruck.objects.filter(fleet_number__iexact=fleet_number).exists():
                self.add_error('fleet_number', 'A truck with this fleet number already exists.')
            if number_plate and CraneTruck.objects.filter(number_plate__iexact=number_plate).exists():
                self.add_error('number_plate', 'A truck with this number plate already exists.')
        return cleaned

class CraneRequestForm(forms.ModelForm):
    class Meta:
        model = CraneRequest
        fields = ['depot', 'purpose', 'location', 'requested_date', 'time_window', 'notes']
        widgets = {
            'depot': forms.Select(attrs={'class': 'form-select'}),
            'purpose': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'requested_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'time_window': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 09:00-12:00'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        user_region = kwargs.pop('user_region', None)
        user_depot = kwargs.pop('user_depot', None)
        lock_depot = kwargs.pop('lock_depot', False)
        super().__init__(*args, **kwargs)
        qs = Depots.objects.all()
        if user_region:
            qs = qs.filter(region=user_region)
        # If a depot foreperson is creating the request, lock to their depot
        if user_depot:
            qs = qs.filter(id=user_depot.id)
        self.fields['depot'].queryset = qs.order_by('depot')
        # Disable the field if locked
        if lock_depot and user_depot:
            self.fields['depot'].initial = user_depot
            self.fields['depot'].disabled = True
        # Friendlier labels
        self.fields['purpose'].label = 'Job to be done'
        self.fields['purpose'].help_text = 'What task should the crane perform at the depot?'
        self.fields['location'].label = 'Work location (at depot/nearby)'
        self.fields['requested_date'].label = 'Preferred date'
        self.fields['time_window'].label = 'Preferred time window'
        self.fields['notes'].label = 'Additional notes'

class CraneAssignmentForm(forms.ModelForm):
    class Meta:
        model = CraneRequest
        fields = ['assigned_truck', 'assigned_operator', 'status']

    def __init__(self, *args, **kwargs):
        # Accept user_region to scope operator options
        user_region = kwargs.pop('user_region', None)
        super().__init__(*args, **kwargs)
        # Only available/in_service trucks
        self.fields['assigned_truck'].queryset = CraneTruck.objects.filter(status__in=['available', 'in_service'])
        self.fields['assigned_truck'].widget.attrs.update({'class': 'form-select'})
        # Operators filtered by region if provided
        try:
            from .central_roles import FaultLocatorRoleManager
            op_qs = FaultLocatorRoleManager.get_users_with_role(FaultLocatorRoleManager.CRANE_OPERATOR)
            op_qs = op_qs.filter(is_active=True)
        except Exception:
            op_qs = UserProfile.objects.filter(is_active=True)
        if user_region:
            op_qs = op_qs.filter(region=user_region)
        self.fields['assigned_operator'].queryset = op_qs.order_by('last_name', 'first_name')
        self.fields['assigned_operator'].widget.attrs.update({'class': 'form-select select2', 'data-placeholder': 'Search operator...'})
        self.fields['status'].widget.attrs.update({'class': 'form-select'})

class CraneJobReportForm(forms.ModelForm):
    class Meta:
        model = CraneJobReport
        fields = ['completion_notes', 'started_at', 'start_mileage_km']
        widgets = {
            'completion_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'started_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'start_mileage_km': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }

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


class TeamDepotAssignmentForm(forms.Form):
    """Simple form for assigning a team to a depot from team overview"""
    depot = forms.ModelChoiceField(
        queryset=Depots.objects.all(),
        empty_label="Select a depot...",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'depot-select'
        })
    )
    deployment_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter deployment notes (optional)...'
        })
    )
    
    def __init__(self, *args, **kwargs):
        user_region = kwargs.pop('user_region', None)
        super().__init__(*args, **kwargs)
        
        # Filter depots by region if user_region is provided
        if user_region:
            self.fields['depot'].queryset = self.fields['depot'].queryset.filter(
                region=user_region
            )
        
        self.fields['depot'].queryset = self.fields['depot'].queryset.order_by('depot')
    
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

class VehicleForm(forms.ModelForm):
    """Form for adding and editing vehicles"""
    class Meta:
        model = Vehicle
        fields = ['fleet_number', 'reg_number', 'odometer_km', 'status']
        widgets = {
            'fleet_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., FL001'
            }),
            'reg_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., ABC-123'
            }),
            'odometer_km': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': 'Current odometer reading'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            })
        }
    
    def clean_odometer_km(self):
        """Ensure odometer doesn't decrease"""
        odometer = self.cleaned_data.get('odometer_km')
        if self.instance and self.instance.pk:
            original_odometer = self.instance.odometer_km
            if odometer < original_odometer:
                raise forms.ValidationError(f"Odometer cannot be less than current reading ({original_odometer} km)")
        return odometer

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
        team = kwargs.pop('team', None)
        super().__init__(*args, **kwargs)
        
        # Filter out users who can't be team leaders
        # Import here to avoid circular imports
        from .views import is_depot_foreperson, is_senior_foreman
        
        base_queryset = UserProfile.objects.filter(is_active=True)
        
        valid_leaders = []
        for user in base_queryset:
            # Check if user is already in another team (as member or leader)
            if team:
                # If editing existing team, allow current team leader
                if user == team.team_leader:
                    valid_leaders.append(user.id)
                    continue
                
                # Exclude if user is in another team
                if user.fault_locator_teams.exclude(id=team.id).exists():
                    continue
                
                # Exclude if user is leader of another team
                if FaultLocatorTeam.objects.filter(team_leader=user).exclude(id=team.id).exists():
                    continue
            else:
                # For new teams, exclude users already in any team
                if user.fault_locator_teams.exists():
                    continue
                
                # Exclude if user is leader of any team
                if FaultLocatorTeam.objects.filter(team_leader=user).exists():
                    continue
            
            # Check if user is a depot foreperson or senior foreperson
            if is_depot_foreperson(user) or is_senior_foreman(user):
                continue
            
            valid_leaders.append(user.id)
        
        self.fields['team_leader'].queryset = base_queryset.filter(
            id__in=valid_leaders
        ).order_by('last_name', 'first_name')
        
        self.fields['team_leader'].widget.attrs.update({
            'class': 'form-select'
        })
    
    def clean_team_leader(self):
        """Validate that selected team leader can be assigned"""
        team_leader = self.cleaned_data.get('team_leader')
        if not team_leader:
            return team_leader
        
        # Import here to avoid circular imports
        from .views import can_user_be_added_to_team
        
        # Get the team instance if editing existing team
        team = self.instance if self.instance.pk else None
        
        can_add, reason = can_user_be_added_to_team(team_leader, team)
        if not can_add:
            raise forms.ValidationError(f"Cannot assign {team_leader.get_full_name()} as team leader: {reason}")
        
        return team_leader

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
        fields = ['description', 'depot', 'vvip', 'priority', 'voltage', 'backfeed', 'clients_affected']
    
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
        self.fields['vvip'].widget = forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
        self.fields['priority'].widget.attrs.update({
            'class': 'form-select'
        })
        self.fields['voltage'].widget = forms.Select(attrs={
            'class': 'form-control',
        })
        self.fields['backfeed'].widget = forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
        self.fields['clients_affected'].widget = forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Number of clients affected',
            'min': '0'
        })
        
        # Add field labels and help text
        self.fields['vvip'].label = 'VVIP Fault'
        self.fields['vvip'].help_text = 'Check if this is a VVIP fault (takes absolute priority)'
        
        # Ensure voltage choices are explicitly set and include a prompt
        try:
            self.fields['voltage'].choices = [('', 'Select voltage level...')] + list(Fault.VOLTAGE_CHOICES)
        except Exception:
            pass
        
        self.fields['voltage'].label = 'Voltage Level'
        self.fields['voltage'].help_text = 'Select the voltage level for this fault'
        self.fields['backfeed'].label = 'Backfeed Available'
        self.fields['backfeed'].help_text = 'Check if backfeed is available'
        self.fields['clients_affected'].label = 'Clients Affected'
        self.fields['clients_affected'].help_text = 'Number of clients affected'
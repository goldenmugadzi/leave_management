from django.db import models
from it.users.models import UserProfile, Depots

class FaultLocatorDevice(models.Model):
    """Fault locator devices/machines used by teams"""
    serial_number = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('available', 'Available'),
        ('assigned', 'Assigned to Team'),
        ('maintenance', 'Under Maintenance'),
        ('retired', 'Retired')
    ], default='available')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.serial_number

class FaultLocatorTeam(models.Model):
    """Teams that perform fault location work"""
    name = models.CharField(max_length=100, unique=True)
    team_leader = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='led_teams', help_text="Team leader who reports fault clearance")
    members = models.ManyToManyField(UserProfile, related_name='fault_locator_teams', blank=True)
    current_depot = models.ForeignKey(Depots, on_delete=models.SET_NULL, null=True, blank=True)
    assigned_at = models.DateTimeField(null=True, blank=True)
    assigned_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='team_assignments_made')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name
    
    def get_team_leader_name(self):
        return self.team_leader.get_full_name() if self.team_leader else "No Leader Assigned"

class Fault(models.Model):
    """Fault reports that need to be located"""
    description = models.CharField(max_length=255)
    depot = models.ForeignKey(Depots, on_delete=models.CASCADE)
    reported_at = models.DateTimeField(auto_now_add=True)
    reported_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='reported_faults')
    status = models.CharField(max_length=30, choices=[
        ('requested', 'Requested'),
        ('assigned', 'Assigned'),
        ('located', 'Located'),
        ('verified', 'Verified by Foreperson'),
        ('closed', 'Closed'),
    ], default='requested')
    priority = models.IntegerField(default=1, choices=[
        (1, 'Low'),
        (2, 'Medium'), 
        (3, 'High'),
        (4, 'Critical')
    ])
    prioritized_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, 
                                     null=True, blank=True, related_name='fault_priorities_set')
    prioritized_at = models.DateTimeField(null=True, blank=True)
    
    # Fault technical details
    VOLTAGE_CHOICES = [
        ('0.4', '0.4kV (Low Voltage)'),
        ('11', '11kV'),
        ('22', '22kV'),
        ('33', '33kV'),
        ('66', '66kV'),
        ('132', '132kV'),
        ('220', '220kV'),
        ('400', '400kV'),
    ]
    
    voltage = models.CharField(max_length=10, choices=VOLTAGE_CHOICES, null=True, blank=True,
                              help_text="Select voltage level")
    backfeed = models.BooleanField(default=False, help_text="Is backfeed available?")
    clients_affected = models.PositiveIntegerField(null=True, blank=True,
                                                 help_text="Number of clients affected by this fault")
    
    # Additional fields for role-based workflow
    foreperson_notes = models.TextField(blank=True, help_text="Notes from depot foreperson")
    team_leader_notes = models.TextField(blank=True, help_text="Notes from team leader")
    location_details = models.TextField(blank=True, help_text="Detailed location information")
    
    # Verification fields
    verified_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='verified_faults', help_text="Foreperson who verified the fault clearance")
    verified_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Fault at {self.depot.depot}: {self.description[:30]}"
    
    def can_be_assigned_by(self, user):
        """Check if user can assign this fault"""
        # Senior foremen can assign any fault
        if self.is_senior_foreman(user):
            return True
        # Depot forepersons can assign faults at their depot
        if self.is_depot_foreperson(user) and user.depot and self.depot.code == user.depot.code:
            return True
        return False
    
    def can_be_reported_by(self, user):
        """Check if user can report/clear this fault"""
        # Team leaders of assigned teams can report
        assignment = self.faultassignment_set.filter(located_at__isnull=True).first()
        if assignment and assignment.team.team_leader == user:
            return True
        # Forepersons at the depot can also report
        return self.can_be_assigned_by(user)
    
    @staticmethod
    def is_senior_foreman(user):
        """Check if user is senior foreman"""
        if not user or not hasattr(user, 'designation') or not user.designation:
            return False
        try:
            designation_desc = str(user.designation.description).lower()
            return 'senior' in designation_desc and ('foreman' in designation_desc or 'foreperson' in designation_desc)
        except:
            return False
    
    @staticmethod
    def is_depot_foreperson(user):
        """Check if user is depot foreperson"""
        if not user or not hasattr(user, 'designation') or not user.designation:
            return False
        try:
            designation_desc = str(user.designation.description).lower()
            return ('foreperson' in designation_desc or 'foreman' in designation_desc) and 'senior' not in designation_desc
        except:
            return False

class FaultAssignment(models.Model):
    """Assignment of faults to teams with devices"""
    fault = models.ForeignKey(Fault, on_delete=models.CASCADE)
    team = models.ForeignKey(FaultLocatorTeam, on_delete=models.CASCADE)
    device = models.ForeignKey(FaultLocatorDevice, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='fault_assignments_made')
    located_at = models.DateTimeField(null=True, blank=True)
    located_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='faults_located', help_text="Team leader who reported the fault as located")
    
    # Work progress tracking
    work_started_at = models.DateTimeField(null=True, blank=True)
    estimated_completion = models.DateTimeField(null=True, blank=True)
    actual_completion = models.DateTimeField(null=True, blank=True)
    work_notes = models.TextField(blank=True, help_text="Progress notes from team")

    def __str__(self):
        return f"{self.fault} assigned to {self.team} with {self.device}"
    
    def get_duration(self):
        """Get time taken to locate fault"""
        if self.located_at:
            return self.located_at - self.assigned_at
        return None

class FaultLocatorDeviceAssignment(models.Model):
    """Assignment of devices to teams by senior foremen"""
    device = models.ForeignKey(FaultLocatorDevice, on_delete=models.CASCADE)
    team = models.ForeignKey(FaultLocatorTeam, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='device_assignments_made', help_text="Senior foreman who made assignment")
    notes = models.TextField(blank=True, help_text="Assignment notes")

    def __str__(self):
        return f"{self.device} -> {self.team} ({self.assigned_at:%Y-%m-%d})"
    
    class Meta:
        unique_together = ['device', 'team']  # One device per team, one team per device

class TeamDeployment(models.Model):
    """Deployment of teams to depots by senior foremen"""
    team = models.ForeignKey(FaultLocatorTeam, on_delete=models.CASCADE)
    depot = models.ForeignKey(Depots, on_delete=models.CASCADE)
    deployed_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='deployments_made',
                                   help_text="Senior foreman who deployed the team")
    deployed_at = models.DateTimeField(auto_now_add=True)
    recalled_at = models.DateTimeField(null=True, blank=True)
    recalled_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='deployments_recalled')
    deployment_notes = models.TextField(blank=True, help_text="Deployment instructions")
    recall_notes = models.TextField(blank=True, help_text="Recall reason/notes")
    
    class Meta:
        unique_together = ['team', 'depot', 'deployed_at']
    
    def __str__(self):
        return f"{self.team.name} deployed to {self.depot.depot}"
    
    def is_active(self):
        return self.recalled_at is None

# Role-based permission models
class FaultLocatorRole(models.Model):
    """Define roles and permissions in fault locator system"""
    ROLE_CHOICES = [
        ('senior_foreman', 'Senior Foreman'),
        ('depot_foreperson', 'Depot Foreperson'), 
        ('team_leader', 'Team Leader'),
        ('team_member', 'Team Member'),
    ]
    
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='fault_locator_roles')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    depot = models.ForeignKey(Depots, on_delete=models.CASCADE, null=True, blank=True,
                             help_text="Specific depot for depot forepersons")
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='role_assignments_made')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['user', 'role', 'depot']
    
    def __str__(self):
        depot_info = f" at {self.depot.depot}" if self.depot else ""
        return f"{self.user.get_full_name()} - {self.get_role_display()}{depot_info}"
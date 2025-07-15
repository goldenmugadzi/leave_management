"""
Utility functions for working with fault locator roles through the central user roles system.
This module provides helpers to check roles and permissions using the central it.users.models.Roles system.
"""

from it.users.models import UserProfile, Roles, Application
from fault_locator.models import FaultLocatorRole

class FaultLocatorRoleManager:
    """Manager class for fault locator roles using central system"""
    
    APPLICATION_NAME = 'fault_locator'
    
    # Role constants
    SENIOR_FOREMAN = 'senior_foreman'
    DEPOT_FOREPERSON = 'depot_foreperson'
    TEAM_LEADER = 'team_leader'
    TEAM_MEMBER = 'team_member'
    FAULT_REPORTER = 'fault_reporter'
    
    @classmethod
    def get_application(cls):
        """Get the fault locator application object"""
        return Application.objects.filter(name=cls.APPLICATION_NAME).first()
    
    @classmethod
    def get_user_role(cls, user_profile):
        """Get the user's fault locator role from central system"""
        if not user_profile:
            return None
        
        # Use the existing method on UserProfile
        role = user_profile.get_user_role_for_application(cls.APPLICATION_NAME)
        return role.role if role else None
    
    @classmethod
    def get_user_role_display(cls, user_profile):
        """Get the user's fault locator role display name"""
        if not user_profile:
            return None
        
        role = user_profile.get_user_role_for_application(cls.APPLICATION_NAME)
        return role.name if role else None
    
    @classmethod
    def assign_role(cls, user_profile, role_code, assigned_by=None):
        """Assign a fault locator role to a user"""
        try:
            application = cls.get_application()
            if not application:
                raise ValueError("Fault locator application not found. Run setup_fault_locator_roles command first.")
            
            role = Roles.objects.get(
                role=role_code,
                application=cls.APPLICATION_NAME,
                app_id=application
            )
            
            # Use the existing add_role method
            user_profile.add_role(role, cls.APPLICATION_NAME)
            
            # Optionally log the assignment
            if assigned_by:
                print(f"Role '{role.name}' assigned to {user_profile.username} by {assigned_by.username}")
            
            return True
            
        except Roles.DoesNotExist:
            raise ValueError(f"Role '{role_code}' not found for fault locator application")
        except Exception as e:
            print(f"Error assigning role: {str(e)}")
            return False
    
    @classmethod
    def remove_role(cls, user_profile):
        """Remove fault locator role from user"""
        try:
            application = cls.get_application()
            if application:
                user_profile.roles.filter(
                    application=cls.APPLICATION_NAME,
                    app_id=application
                ).delete()
            return True
        except Exception as e:
            print(f"Error removing role: {str(e)}")
            return False
    
    @classmethod
    def has_role(cls, user_profile, role_code):
        """Check if user has specific fault locator role"""
        user_role = cls.get_user_role(user_profile)
        return user_role == role_code
    
    @classmethod
    def has_any_role(cls, user_profile):
        """Check if user has any fault locator role"""
        return cls.get_user_role(user_profile) is not None
    
    @classmethod
    def get_users_with_role(cls, role_code):
        """Get all users with a specific fault locator role"""
        try:
            application = cls.get_application()
            if not application:
                return UserProfile.objects.none()
            
            role = Roles.objects.get(
                role=role_code,
                application=cls.APPLICATION_NAME,
                app_id=application
            )
            
            return UserProfile.objects.filter(roles=role)
            
        except Roles.DoesNotExist:
            return UserProfile.objects.none()
    
    @classmethod
    def get_available_roles(cls):
        """Get all available fault locator roles"""
        application = cls.get_application()
        if not application:
            return []
        
        return Roles.objects.filter(
            application=cls.APPLICATION_NAME,
            app_id=application
        ).order_by('name')

# Permission checking functions using central roles
def get_user_fault_locator_role(user_profile):
    """Get the user's primary fault locator role from central system"""
    return FaultLocatorRoleManager.get_user_role(user_profile)

def is_senior_foreman(user_profile):
    """Check if user is a senior foreman using central roles"""
    return FaultLocatorRoleManager.has_role(user_profile, FaultLocatorRoleManager.SENIOR_FOREMAN)

def is_depot_foreperson(user_profile, depot_code=None):
    """Check if user is depot foreperson using central roles"""
    if not FaultLocatorRoleManager.has_role(user_profile, FaultLocatorRoleManager.DEPOT_FOREPERSON):
        return False
    
    # If depot_code is provided, check if user is assigned to that depot
    if depot_code:
        if hasattr(user_profile, 'depot') and user_profile.depot:
            if isinstance(depot_code, str):
                return user_profile.depot.code == depot_code
            else:
                return user_profile.depot == depot_code
    
    return True

def is_team_leader(user_profile):
    """Check if user is a team leader using central roles"""
    return FaultLocatorRoleManager.has_role(user_profile, FaultLocatorRoleManager.TEAM_LEADER)

def is_team_member(user_profile):
    """Check if user is a team member using central roles"""
    return FaultLocatorRoleManager.has_role(user_profile, FaultLocatorRoleManager.TEAM_MEMBER)

def is_fault_reporter(user_profile):
    """Check if user can report faults using central roles"""
    return FaultLocatorRoleManager.has_role(user_profile, FaultLocatorRoleManager.FAULT_REPORTER)

def can_assign_faults(user_profile, depot=None):
    """Check if user can assign faults at given depot"""
    if is_senior_foreman(user_profile):
        return True
    
    if depot and is_depot_foreperson(user_profile):
        if hasattr(user_profile, 'depot') and user_profile.depot:
            return user_profile.depot == depot or user_profile.depot.code == depot.code
    
    return False

def can_deploy_teams(user_profile):
    """Check if user can deploy teams to depots"""
    return is_senior_foreman(user_profile)

def can_manage_devices(user_profile):
    """Check if user can manage fault locator devices"""
    return is_senior_foreman(user_profile)

def can_create_teams(user_profile):
    """Check if user can create and manage teams"""
    return is_senior_foreman(user_profile)

def can_report_fault_status(user_profile, fault):
    """Check if user can report on fault status"""
    # Team leaders can report for their assignments
    if is_team_leader(user_profile):
        from fault_locator.models import FaultAssignment
        assignment = FaultAssignment.objects.filter(
            fault=fault, 
            team__team_leader=user_profile,
            located_at__isnull=True
        ).first()
        if assignment:
            return True
    
    # Forepersons can also report at their depot
    if is_depot_foreperson(user_profile):
        if hasattr(user_profile, 'depot') and user_profile.depot:
            return fault.depot == user_profile.depot
    
    # Senior foremen can report on any fault
    return is_senior_foreman(user_profile)

def has_fault_locator_permissions(user_profile):
    """Check if user has any fault locator system permissions"""
    if not user_profile:
        return False
    
    # Check for formal roles first
    if FaultLocatorRoleManager.has_any_role(user_profile):
        return True
    
    # Check if user is a team member or team leader
    from .models import FaultLocatorTeam
    
    # Check if user is a team leader
    if FaultLocatorTeam.objects.filter(team_leader=user_profile).exists():
        return True
    
    # Check if user is a team member
    if FaultLocatorTeam.objects.filter(members=user_profile).exists():
        return True
    
    return False

# Role assignment helpers
def assign_fault_locator_role(user_profile, role_code, assigned_by=None):
    """Assign a fault locator role to a user"""
    return FaultLocatorRoleManager.assign_role(user_profile, role_code, assigned_by)

def remove_fault_locator_role(user_profile):
    """Remove fault locator role from user"""
    return FaultLocatorRoleManager.remove_role(user_profile)

# Migration helper
def migrate_legacy_roles():
    """Migrate from FaultLocatorRole to central roles system"""
    migrated = 0
    errors = []
    
    for old_role in FaultLocatorRole.objects.filter(is_active=True):
        try:
            success = assign_fault_locator_role(
                old_role.user, 
                old_role.role, 
                old_role.assigned_by
            )
            if success:
                migrated += 1
                old_role.is_active = False
                old_role.save()
        except Exception as e:
            errors.append(f"Error migrating {old_role.user.username}: {str(e)}")
    
    return migrated, errors

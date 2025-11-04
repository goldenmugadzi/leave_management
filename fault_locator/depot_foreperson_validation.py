"""
Validation logic for depot foreperson assignments
"""

from it.users.models import UserProfile, Depots
from fault_locator.central_roles import FaultLocatorRoleManager, is_depot_foreperson_by_designation


def validate_depot_foreperson_assignment(user_profile, depot, exclude_user=None):
    """
    Validate that a depot foreperson can be assigned to a specific depot.
    
    Args:
        user_profile: UserProfile instance to be assigned as depot foreperson
        depot: Depot instance where user will be assigned
        exclude_user: UserProfile instance to exclude from validation (for updates)
    
    Returns:
        tuple: (is_valid, error_message)
    """
    
    # Check if user is qualified to be a depot foreperson
    if not is_depot_foreperson_by_designation(user_profile):
        return False, f"{user_profile.get_full_name()} is not qualified to be a depot foreperson (check designation)"
    
    # Check if depot already has a depot foreperson
    existing_forepersons = get_depot_forepersons(depot)
    
    if exclude_user:
        existing_forepersons = existing_forepersons.exclude(id=exclude_user.id)
    
    if existing_forepersons.exists():
        existing_fp = existing_forepersons.first()
        return False, f"Depot '{depot.depot}' already has a depot foreperson: {existing_fp.get_full_name()}"
    
    return True, ""


def get_depot_forepersons(depot):
    """
    Get all depot forepersons assigned to a specific depot.
    
    Args:
        depot: Depot instance
    
    Returns:
        QuerySet: UserProfile instances who are depot forepersons at this depot
    """
    return UserProfile.objects.filter(
        depot=depot,
        designation__description__icontains='foreperson'
    ).exclude(
        designation__description__icontains='senior'
    )


def get_available_depots_for_foreperson_assignment():
    """
    Get all depots that don't have a depot foreperson assigned yet.
    
    Returns:
        QuerySet: Depots that are available for depot foreperson assignment
    """
    # Get all depots
    all_depots = Depots.objects.all()
    
    # Get depots that already have forepersons
    occupied_depot_ids = []
    for depot in all_depots:
        if get_depot_forepersons(depot).exists():
            occupied_depot_ids.append(depot.id)
    
    # Return depots without forepersons
    return all_depots.exclude(id__in=occupied_depot_ids).order_by('depot')


def get_depot_foreperson_for_depot(depot):
    """
    Get the depot foreperson assigned to a specific depot.
    
    Args:
        depot: Depot instance
    
    Returns:
        UserProfile or None: The depot foreperson for this depot, or None if none assigned
    """
    return get_depot_forepersons(depot).first()


def can_reassign_depot_foreperson(current_user, target_depot):
    """
    Check if a depot foreperson can be reassigned to a different depot.
    
    Args:
        current_user: UserProfile instance of the current depot foreperson
        target_depot: Depot instance where user wants to be reassigned
    
    Returns:
        tuple: (can_reassign, error_message)
    """
    # Check if user is qualified
    if not is_depot_foreperson_by_designation(current_user):
        return False, f"{current_user.get_full_name()} is not qualified to be a depot foreperson"
    
    # Check if target depot is available (excluding current user)
    return validate_depot_foreperson_assignment(current_user, target_depot, exclude_user=current_user)


def validate_depot_foreperson_removal(user_profile, depot):
    """
    Validate that a depot foreperson can be removed from a depot.
    
    Args:
        user_profile: UserProfile instance to be removed as depot foreperson
        depot: Depot instance from which user will be removed
    
    Returns:
        tuple: (is_valid, error_message)
    """
    # Check if user is actually assigned to this depot
    if not (hasattr(user_profile, 'depot') and user_profile.depot == depot):
        return False, f"{user_profile.get_full_name()} is not assigned to depot '{depot.depot}'"
    
    # Check if user is actually a depot foreperson
    if not is_depot_foreperson_by_designation(user_profile):
        return False, f"{user_profile.get_full_name()} is not a depot foreperson"
    
    # Additional checks can be added here (e.g., active faults, deployed teams, etc.)
    
    return True, ""


def get_depot_assignment_summary():
    """
    Get a summary of depot foreperson assignments across all depots.
    
    Returns:
        dict: Summary information about depot assignments
    """
    all_depots = Depots.objects.all().order_by('depot')
    occupied_depots = 0
    available_depots = 0
    assignments = []
    
    for depot in all_depots:
        foreperson = get_depot_foreperson_for_depot(depot)
        if foreperson:
            occupied_depots += 1
            assignments.append({
                'depot': depot,
                'foreperson': foreperson,
                'status': 'occupied'
            })
        else:
            available_depots += 1
            assignments.append({
                'depot': depot,
                'foreperson': None,
                'status': 'available'
            })
    
    return {
        'total_depots': all_depots.count(),
        'occupied_depots': occupied_depots,
        'available_depots': available_depots,
        'assignments': assignments
    }

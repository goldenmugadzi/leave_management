#!/usr/bin/env python3
"""
Add Sample Team Deployment Data
This script adds sample deployment data for testing.
"""

import os
import django
import sys
from datetime import datetime, timedelta

# Add the project directory to the Python path
sys.path.append('d:\\b')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from fault_locator.models import FaultLocatorTeam, TeamDeployment
from it.users.models import UserProfile, Depots
from django.utils import timezone
from django.db import transaction

def add_sample_deployments():
    print("=== ADDING SAMPLE TEAM DEPLOYMENTS ===")
    print()
    
    # Get some teams with devices
    teams_with_devices = FaultLocatorTeam.objects.filter(
        faultlocatordeviceassignment__isnull=False
    )[:2]  # Get first 2 teams
    
    # Get some depots
    depots = Depots.objects.all()[:3]  # Get first 3 depots
    
    # Get a senior foreman (or use first user)
    senior_foreman = UserProfile.objects.first()
    
    print(f"Teams with devices: {teams_with_devices.count()}")
    print(f"Available depots: {depots.count()}")
    print(f"Senior foreman: {senior_foreman.get_full_name() if senior_foreman else 'None'}")
    print()
    
    deployments_created = 0
    
    for i, team in enumerate(teams_with_devices):
        if i < len(depots):
            depot = depots[i]
            
            # Check if team is already deployed
            if team.current_depot:
                print(f"Team '{team.name}' is already deployed to {team.current_depot.depot}")
                continue
            
            # Create deployment record
            deployment = TeamDeployment.objects.create(
                team=team,
                depot=depot,
                deployed_by=senior_foreman,
                deployed_at=timezone.now() - timedelta(days=i+1),  # Stagger deployments
                deployment_notes=f"Sample deployment of {team.name} to {depot.depot}"
            )
            
            # Update team's current depot
            team.current_depot = depot
            team.assigned_at = deployment.deployed_at
            team.assigned_by = senior_foreman
            team.save()
            
            print(f"✅ Deployed team '{team.name}' to {depot.depot}")
            deployments_created += 1
        else:
            print(f"⚠️  No depot available for team '{team.name}'")
    
    print()
    print(f"Created {deployments_created} deployments")
    
    # Show updated team status
    print("\n=== UPDATED TEAM STATUS ===")
    for team in FaultLocatorTeam.objects.all():
        status = "Deployed" if team.current_depot else "Available"
        location = team.current_depot.depot if team.current_depot else "Base"
        device_status = "With Device" if team.faultlocatordeviceassignment_set.exists() else "No Device"
        
        print(f"Team '{team.name}': {status} at {location} ({device_status})")

if __name__ == "__main__":
    with transaction.atomic():
        add_sample_deployments()

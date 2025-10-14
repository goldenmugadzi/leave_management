#!/usr/bin/env python
"""
Standalone test script to simulate the fault locator role audit logic
without requiring full database migrations.
"""

import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure Django settings
if not settings.configured:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings_test')
    django.setup()

from django.core.management import call_command
from django.test import TestCase, TransactionTestCase
from django.db import connection

# Import models after Django setup
from it.users.models import UserProfile, Application, Roles, Depots, Designations
from fault_locator.models import FaultLocatorRole, FaultLocatorTeam


class RoleAuditSimulationTest(TransactionTestCase):
    """Simulate role audit logic with test data."""
    
    def setUp(self):
        """Create test data for simulation."""
        # Create application
        self.app = Application.objects.create(
            name='fault_locator',
            fullname='Fault Locator System'
        )
        
        # Create roles
        self.senior_role = Roles.objects.create(
            role='senior_foreman',
            name='Senior Foreman',
            description='Senior foreman role',
            application='fault_locator',
            app_id=self.app
        )
        
        self.depot_role = Roles.objects.create(
            role='depot_foreperson',
            name='Depot Foreperson',
            description='Depot foreperson role',
            application='fault_locator',
            app_id=self.app
        )
        
        # Create test depot
        try:
            from it.users.models import Districts, Regions
            region = Regions.objects.create(region='Test Region', code='TR')
            district = Districts.objects.create(district='Test District', code='TD', region_id='TR')
            self.depot = Depots.objects.create(
                depot='Test Depot',
                code='TD001',
                district=district,
                region=region
            )
        except:
            # Simplified for test
            self.depot = None
        
        # Create test designation
        try:
            self.designation = Designations.objects.create(
                identifier='SF001',
                description='Senior Foreman Operations'
            )
        except:
            self.designation = None
        
        # Create test users
        self.user1 = UserProfile.objects.create_user(
            username='SF001',
            first_name='John',
            last_name='Senior',
            designation=self.designation,
            depot=self.depot
        )
        
        self.user2 = UserProfile.objects.create_user(
            username='DF001',
            first_name='Jane',
            last_name='Depot',
            depot=self.depot
        )
        
        self.user3 = UserProfile.objects.create_user(
            username='TL001',
            first_name='Mike',
            last_name='Leader'
        )
        
        # Assign central roles
        self.user1.roles.add(self.senior_role)
        self.user2.roles.add(self.depot_role)
        
        # Create legacy role for user3
        FaultLocatorRole.objects.create(
            user=self.user3,
            role='team_leader',
            is_active=True
        )
        
        # Create team with user3 as leader
        self.team = FaultLocatorTeam.objects.create(
            name='Test Team Alpha',
            team_leader=self.user3
        )
        
        # Add user1 as team member
        self.team.members.add(self.user1)
    
    def test_audit_logic_simulation(self):
        """Test the audit logic with our test data."""
        print("\n=== FAULT LOCATOR ROLE AUDIT SIMULATION ===")
        
        # Import the core logic from our command
        from fault_locator.management.commands.audit_fault_locator_roles import (
            compute_effective_role,
            infer_designation_role,
            ANOMALY_DEFINITIONS
        )
        
        users = UserProfile.objects.all()
        results = []
        
        for user in users:
            # Get central roles
            central_roles = list(user.roles.filter(app_id=self.app))
            
            # Get legacy roles
            legacy_roles = list(FaultLocatorRole.objects.filter(user=user, is_active=True))
            
            # Get team assignments
            team_leader_team = FaultLocatorTeam.objects.filter(team_leader=user).first()
            member_teams = list(user.fault_locator_teams.all())
            
            # Infer designation role
            designation_role = infer_designation_role(user)
            
            # Compute effective role
            effective_role = compute_effective_role(
                user, central_roles, legacy_roles, team_leader_team, member_teams, designation_role
            )
            
            # Detect anomalies
            anomalies = []
            if len(central_roles) > 1:
                anomalies.append('MULTIPLE_CENTRAL_ROLES')
            if central_roles and legacy_roles:
                anomalies.append('LEGACY_AND_CENTRAL')
            if legacy_roles and not central_roles:
                anomalies.append('LEGACY_ACTIVE')
            if (effective_role == 'depot_foreperson' or any(r.role == 'depot_foreperson' for r in central_roles + legacy_roles)) and not user.depot:
                anomalies.append('DEPOT_FOREPERSON_WITHOUT_DEPOT')
            if team_leader_team and not central_roles and not legacy_roles:
                anomalies.append('TEAM_LEADER_NO_ROLE')
            if member_teams and not team_leader_team and not central_roles and not legacy_roles:
                anomalies.append('TEAM_MEMBER_NO_ROLE')
            if designation_role and not central_roles and not legacy_roles:
                anomalies.append('INFERRED_ONLY')
            
            result = {
                'username': user.username,
                'name': f"{user.last_name} {user.first_name}".strip(),
                'central_roles': [r.role for r in central_roles],
                'legacy_roles': [r.role for r in legacy_roles],
                'team_leader': bool(team_leader_team),
                'team_member': len(member_teams) > 0,
                'designation_role': designation_role,
                'effective_role': effective_role,
                'anomalies': anomalies
            }
            results.append(result)
            
            print(f"\nUser: {result['username']} ({result['name']})")
            print(f"  Central Roles: {result['central_roles']}")
            print(f"  Legacy Roles: {result['legacy_roles']}")
            print(f"  Team Leader: {result['team_leader']}")
            print(f"  Team Member: {result['team_member']}")
            print(f"  Designation Role: {result['designation_role']}")
            print(f"  Effective Role: {result['effective_role']}")
            print(f"  Anomalies: {result['anomalies']}")
        
        print(f"\n=== SIMULATION COMPLETE ({len(results)} users processed) ===")
        
        # Validate expected results
        self.assertEqual(len(results), 3, "Should process 3 test users")
        
        # Check user1 (senior foreman with central role)
        user1_result = next(r for r in results if r['username'] == 'SF001')
        self.assertEqual(user1_result['effective_role'], 'senior_foreman')
        self.assertIn('senior_foreman', user1_result['central_roles'])
        self.assertEqual(user1_result['designation_role'], 'senior_foreman')
        
        # Check user2 (depot foreperson with central role)
        user2_result = next(r for r in results if r['username'] == 'DF001')
        self.assertEqual(user2_result['effective_role'], 'depot_foreperson')
        self.assertIn('depot_foreperson', user2_result['central_roles'])
        
        # Check user3 (team leader with legacy role)
        user3_result = next(r for r in results if r['username'] == 'TL001')
        self.assertEqual(user3_result['effective_role'], 'team_leader')
        self.assertIn('team_leader', user3_result['legacy_roles'])
        self.assertIn('LEGACY_ACTIVE', user3_result['anomalies'])
        
        print("\n✅ All validation checks passed!")
        return results


def run_simulation():
    """Run the simulation test."""
    from django.test.utils import setup_test_environment, teardown_test_environment
    from django.db import connection
    from django.core.management.color import no_style
    
    setup_test_environment()
    
    # Create test database
    connection.creation.create_test_db(verbosity=1, autoclobber=True, serialize=False)
    
    try:
        # Run the test
        test = RoleAuditSimulationTest()
        test.setUp()
        results = test.test_audit_logic_simulation()
        
        print(f"\n📊 SUMMARY:")
        print(f"   Total users: {len(results)}")
        anomaly_counts = {}
        for result in results:
            for anomaly in result['anomalies']:
                anomaly_counts[anomaly] = anomaly_counts.get(anomaly, 0) + 1
        
        if anomaly_counts:
            print(f"   Anomalies detected:")
            for anomaly, count in anomaly_counts.items():
                print(f"     {anomaly}: {count}")
        else:
            print(f"   No anomalies detected")
            
    finally:
        # Clean up test database
        connection.creation.destroy_test_db('test_' + connection.settings_dict['NAME'], verbosity=1)
        teardown_test_environment()


if __name__ == '__main__':
    run_simulation()
#!/usr/bin/env python
"""Test edit_team template specifically"""

import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from django.test import RequestFactory
from django.template.loader import render_to_string
from django.contrib.auth.models import AnonymousUser
from it.users.models import UserProfile
from fault_locator.models import FaultLocatorTeam

def test_edit_team_template():
    """Test that edit_team template renders without URL errors"""
    print("Testing edit_team template...")
    
    try:
        # Create a mock team
        team_data = {
            'id': 1,
            'name': 'Test Team',
            'team_leader': None,
            'members': [],
            'deployment_status': 'ready',
            'created_at': '2025-07-15'
        }
        
        # Create context similar to what the view would pass
        context = {
            'team': type('Team', (), team_data),
            'members': [],
            'available_users': [],
            'user_profile': None,
            'can_edit': True,
            'can_delete': True,
            'can_assign_faults': True,
            'can_deploy': True,
            'is_senior_foreman': False,
            'current_assignments': [],
            'device_assignment': None,
            'deployment': None,
            'role': None,
        }
        
        # Test rendering just the URL part
        template_content = """
        <a href="{% url 'assign_fault' %}?team_id={{ team.id }}">Quick Assign</a>
        <a href="{% url 'advanced_fault_assignment' %}">Advanced</a>
        """
        
        from django.template import Template, Context
        template = Template(template_content)
        rendered = template.render(Context(context))
        
        print(f"✅ Template fragment rendered successfully:")
        print(rendered)
        
        # Check for expected URLs
        if '/fault_locator/simple-assign/' in rendered and '/fault_locator/advanced-assign/' in rendered:
            print("✅ All URLs are correctly resolved")
            return True
        else:
            print("❌ Some URLs might not be resolved correctly")
            return False
            
    except Exception as e:
        print(f"❌ Template test failed: {e}")
        return False

if __name__ == "__main__":
    print("=== Edit Team Template Test ===")
    
    if test_edit_team_template():
        print("\n✅ Edit team template test passed!")
    else:
        print("\n❌ Edit team template test failed.")

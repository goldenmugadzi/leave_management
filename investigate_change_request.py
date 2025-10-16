#!/usr/bin/env python3
"""
Script to investigate change request c07cfa0a-de03-4c8e-b2db-5aab4055031e
and identify incomplete tasks or missing data.
"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.append('/var/www/beii_v1')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from it.change_requests.models import ChangeRequest, ProfileChange, CRApproval
from it.users.models import UserProfile, Application

def investigate_change_request():
    cr_id = "c07cfa0a-de03-4c8e-b2db-5aab4055031e"
    
    try:
        # Get the change request
        change_request = ChangeRequest.objects.get(cr_id=cr_id)
        
        print(f"=== Change Request Investigation: {cr_id} ===")
        print(f"Created by: {change_request.created_by.get_full_name()}")
        print(f"Created at: {change_request.created_at}")
        print(f"Change reason: {change_request.change_reason}")
        print(f"Change description: {change_request.change_description}")
        print(f"Application: {change_request.application}")
        print(f"Creator designation: {change_request.creator_designation}")
        print()
        
        # Check if it's a profile change request
        if hasattr(change_request, 'profile_change') and change_request.profile_change:
            profile_change = change_request.profile_change
            print("=== Profile Change Details ===")
            print(f"User: {profile_change.user.get_full_name()}")
            print(f"User username: {profile_change.user.username}")
            print(f"User designation: {profile_change.user.designation}")
            print(f"User section: {profile_change.user.section}")
            print(f"User district: {profile_change.user.district}")
            print(f"User region: {profile_change.user.region}")
            print(f"Roles to action: {profile_change.roles_to_action}")
            print(f"Roles actions: {profile_change.roles_actions}")
            print()
        
        # Check approvals
        approvals = CRApproval.objects.filter(cr_id=change_request)
        print("=== Approval Status ===")
        if approvals.exists():
            for approval in approvals:
                print(f"Approver: {approval.approver.get_full_name()}")
                print(f"Approver role: {approval.approver_role.role}")
                print(f"Approval status: {approval.approval_status}")
                print(f"Approved at: {approval.approved_at}")
                print(f"Comments: {approval.comments}")
                print("---")
        else:
            print("No approvals found")
        
        print()
        print("=== Analysis ===")
        
        # Check what's missing
        missing_items = []
        
        if not change_request.application:
            missing_items.append("Application not specified")
        
        if hasattr(change_request, 'profile_change') and change_request.profile_change:
            pc = change_request.profile_change
            if not pc.roles_to_action:
                missing_items.append("Roles to action not specified")
            if not pc.roles_actions:
                missing_items.append("Implementation status/roles actions not filled")
        
        # Check approval workflow
        section_head_approved = False
        it_section_head_approved = False
        
        for approval in approvals:
            if approval.approver_role.role == "section_head":
                section_head_approved = approval.approval_status
            elif approval.approver_role.role == "it_section_head":
                it_section_head_approved = approval.approval_status
        
        if not section_head_approved:
            missing_items.append("Section head approval pending")
        if not it_section_head_approved:
            missing_items.append("IT section head approval/implementation pending")
        
        if missing_items:
            print("Issues found:")
            for item in missing_items:
                print(f"- {item}")
        else:
            print("No obvious issues found")
            
        # Check all available applications for reference
        print("\n=== Available Applications ===")
        applications = Application.objects.all()
        for app in applications:
            print(f"- {app.name} (ID: {app.id})")
            
    except ChangeRequest.DoesNotExist:
        print(f"Change request with ID {cr_id} not found")
    except Exception as e:
        print(f"Error investigating change request: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    investigate_change_request()
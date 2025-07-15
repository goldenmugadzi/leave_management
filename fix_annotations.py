#!/usr/bin/env python3
"""
Fix Annotation Issues
This script fixes the annotation mismatch in team overview.
"""

import os
import django
import sys

# Add the project directory to the Python path
sys.path.append('d:\\b')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from fault_locator.models import FaultLocatorTeam
from django.db.models import Count, Q

def fix_annotation_issues():
    print("=== FIXING ANNOTATION ISSUES ===")
    print()
    
    # Check the "jjj" team specifically
    jjj_team = FaultLocatorTeam.objects.get(name='jjj')
    print(f"Team: {jjj_team.name}")
    print(f"ID: {jjj_team.id}")
    
    # Check members directly
    members = jjj_team.members.all()
    print(f"Members count: {members.count()}")
    for member in members:
        print(f"  - {member.id}: {member.get_full_name()} ({member.email})")
    
    # Check for any orphaned member relationships
    from django.db import connection
    cursor = connection.cursor()
    cursor.execute("""
        SELECT * FROM fault_locator_faultlocatorteam_members 
        WHERE faultlocatorteam_id = %s
    """, [jjj_team.id])
    
    relationships = cursor.fetchall()
    print(f"M2M relationships: {len(relationships)}")
    for rel in relationships:
        print(f"  - Team {rel[1]} -> User {rel[2]}")
    
    # Check if there are duplicate relationships
    if len(relationships) != members.count():
        print("❌ MISMATCH: M2M relationships don't match actual members!")
        
        # Clean up by removing all relationships and re-adding
        print("Cleaning up relationships...")
        jjj_team.members.clear()
        
        # Get unique members
        unique_members = list(set(members))
        print(f"Unique members: {len(unique_members)}")
        
        # Re-add members
        for member in unique_members:
            jjj_team.members.add(member)
            print(f"  Added: {member.get_full_name()}")
    
    # Test annotation again
    print("\nTesting annotation after cleanup...")
    team_with_annotation = FaultLocatorTeam.objects.filter(id=jjj_team.id).annotate(
        member_count=Count('members', distinct=True)
    ).first()
    
    print(f"Annotated count: {team_with_annotation.member_count}")
    print(f"Actual count: {team_with_annotation.members.count()}")
    
    if team_with_annotation.member_count == team_with_annotation.members.count():
        print("✅ FIXED: Annotation now matches actual count!")
    else:
        print("❌ STILL BROKEN: Annotation mismatch persists")

if __name__ == "__main__":
    fix_annotation_issues()

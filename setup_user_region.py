#!/usr/bin/env python
"""
Setup script to assign a region to the test user profile.
"""

import os
import sys

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')

import django
django.setup()

# Now import Django modules
from it.users.models import UserProfile, Regions

def assign_region_to_user():
    """Assign a region to the test user profile"""
    
    print("🔧 Assigning region to user profile...")
    
    # Get the first user profile
    user_profile = UserProfile.objects.first()
    if not user_profile:
        print("❌ No user profiles found.")
        return False
    
    # Get the first region
    region = Regions.objects.first()
    if not region:
        print("❌ No regions found.")
        return False
    
    # Assign region to user
    user_profile.region = region
    user_profile.save()
    
    print(f"✅ Assigned region '{region.region}' to user '{user_profile.get_full_name()}'")
    return True

if __name__ == "__main__":
    print("🚀 SETTING UP USER REGION")
    print("=" * 40)
    
    success = assign_region_to_user()
    
    if success:
        print("✅ Setup complete! Running region filtering test again...")
        print("=" * 40)
        
        # Now run the region filtering test
        import subprocess
        result = subprocess.run([sys.executable, 'test_region_filtering.py'], capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
    else:
        print("❌ Setup failed.")

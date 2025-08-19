"""
Safe migration script for asset numbers
This script will migrate your existing asset numbers to the enhanced format
while preserving all existing data as backup
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from ACE2.models import Ace2, AceAssetNumber
from it.users.models import UserProfile
from django.db import transaction

def migrate_all_assets():
    print("=== Starting Asset Number Migration ===")
    
    # Get or create a migration user
    user = UserProfile.objects.filter(is_superuser=True).first()
    if not user:
        user = UserProfile.objects.first()
    
    if not user:
        print("❌ No users found. Please create a user first.")
        return
    
    print(f"Using migration user: {user.get_full_name()} ({user.username})")
    
    # Get ACEs that need migration
    aces_to_migrate = Ace2.objects.exclude(
        asset_number__isnull=True
    ).exclude(
        asset_number__exact=''
    ).filter(
        enhanced_asset_numbers__isnull=True
    )
    
    total_aces = aces_to_migrate.count()
    print(f"Found {total_aces} ACEs to migrate")
    
    if total_aces == 0:
        print("✅ No ACEs need migration")
        return
    
    # Confirm migration
    response = input(f"Do you want to migrate {total_aces} ACEs? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Migration cancelled")
        return
    
    # Perform migration
    migrated_aces = 0
    migrated_assets = 0
    errors = []
    
    print("\nStarting migration...")
    
    for i, ace in enumerate(aces_to_migrate, 1):
        try:
            with transaction.atomic():
                # Parse existing asset numbers
                if ace.asset_number:
                    asset_list = [an.strip() for an in ace.asset_number.split(',') if an.strip()]
                    
                    ace_migrated_count = 0
                    for asset_num in asset_list:
                        # Check if already exists (shouldn't, but just in case)
                        if not ace.enhanced_asset_numbers.filter(asset_number=asset_num).exists():
                            AceAssetNumber.objects.create(
                                ace=ace,
                                asset_number=asset_num,
                                added_by=user,
                                notes="Migrated from legacy system"
                            )
                            ace_migrated_count += 1
                    
                    if ace_migrated_count > 0:
                        migrated_aces += 1
                        migrated_assets += ace_migrated_count
                        
                        # Show progress every 100 ACEs
                        if i % 100 == 0:
                            print(f"Progress: {i}/{total_aces} ACEs processed...")
                
        except Exception as e:
            error_msg = f"ACE {ace.Ace_id2}: {str(e)}"
            errors.append(error_msg)
            print(f"❌ {error_msg}")
    
    print("\n=== Migration Complete ===")
    print(f"✅ Successfully migrated {migrated_assets} asset numbers from {migrated_aces} ACEs")
    
    if errors:
        print(f"❌ {len(errors)} errors occurred:")
        for error in errors[:10]:  # Show first 10 errors
            print(f"   {error}")
        if len(errors) > 10:
            print(f"   ... and {len(errors) - 10} more errors")
    
    # Verify migration
    print("\n=== Verification ===")
    enhanced_count = Ace2.objects.filter(enhanced_asset_numbers__isnull=False).distinct().count()
    print(f"ACEs with enhanced asset numbers: {enhanced_count}")
    
    print("\n✅ Migration completed successfully!")
    print("\nNote: Your original asset_number fields are preserved as backup.")
    print("The enhanced system now manages your asset numbers with better tracking.")

if __name__ == "__main__":
    migrate_all_assets()

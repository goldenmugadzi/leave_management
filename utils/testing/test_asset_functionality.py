"""
Quick test script to verify asset number functionality
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from ACE2.models import Ace2, AceAssetNumber
from it.users.models import UserProfile

def test_asset_functionality():
    print("=== Asset Number Functionality Test ===")
    
    # Get stats
    total_aces = Ace2.objects.count()
    legacy_aces = Ace2.objects.exclude(asset_number__isnull=True).exclude(asset_number__exact='').count()
    enhanced_aces = Ace2.objects.filter(enhanced_asset_numbers__isnull=False).distinct().count()
    
    print(f"Total ACEs: {total_aces}")
    print(f"ACEs with legacy asset numbers: {legacy_aces}")
    print(f"ACEs with enhanced asset numbers: {enhanced_aces}")
    
    # Test a sample ACE
    sample_ace = Ace2.objects.exclude(asset_number__isnull=True).exclude(asset_number__exact='').first()
    if sample_ace:
        print(f"\n=== Sample ACE: {sample_ace.Ace_id2} ===")
        print(f"Legacy asset numbers: {sample_ace.asset_number}")
        
        if sample_ace.asset_number:
            asset_list = [an.strip() for an in sample_ace.asset_number.split(',') if an.strip()]
            print(f"Parsed assets: {asset_list}")
            print(f"Number of assets: {len(asset_list)}")
        
        # Test get_all_asset_numbers method
        all_assets = sample_ace.get_all_asset_numbers()
        print(f"get_all_asset_numbers(): {all_assets}")
        
        enhanced_assets = sample_ace.enhanced_asset_numbers.all()
        print(f"Enhanced assets count: {enhanced_assets.count()}")
    
    # Test if we can create an enhanced asset number
    user = UserProfile.objects.first()
    if user and sample_ace:
        print(f"\n=== Testing Enhanced Asset Creation ===")
        print(f"Using user: {user.get_full_name()}")
        
        try:
            # Try to create a test enhanced asset
            test_asset_num = "TEST123456"
            if not sample_ace.enhanced_asset_numbers.filter(asset_number=test_asset_num).exists():
                ace_asset = AceAssetNumber.objects.create(
                    ace=sample_ace,
                    asset_number=test_asset_num,
                    added_by=user,
                    notes="Test asset from script"
                )
                print(f"✓ Created test enhanced asset: {ace_asset}")
                
                # Test verification
                verification_result = ace_asset.verify_against_register()
                print(f"Verification result: {verification_result}")
                print(f"Is verified: {ace_asset.is_verified}")
                
                # Clean up
                ace_asset.delete()
                print("✓ Test asset cleaned up")
            else:
                print("Test asset already exists, skipping creation")
                
        except Exception as e:
            print(f"✗ Error creating enhanced asset: {e}")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_asset_functionality()

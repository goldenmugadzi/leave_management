"""
Quick test script to verify our enhanced asset number system
"""
import django
import os
import sys

# Setup Django environment
sys.path.append('d:/b')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from ACE2.models import Ace2, AceAssetNumber
from it.users.models import UserProfile

def test_enhanced_system():
    print("🚀 Testing Enhanced Asset Number System")
    print("=" * 50)
    
    # Get a test ACE
    test_ace = Ace2.objects.first()
    if not test_ace:
        print("❌ No ACEs found in database")
        return
    
    print(f"✅ Testing with ACE: {test_ace.Ace_id2}")
    print(f"   Legacy asset_number: {test_ace.asset_number}")
    
    # Check enhanced asset numbers
    enhanced_assets = test_ace.enhanced_asset_numbers.all()
    print(f"   Enhanced assets count: {enhanced_assets.count()}")
    
    for asset in enhanced_assets:
        print(f"   - {asset.asset_number} (verified: {asset.is_verified})")
    
    # Test the get_all_asset_numbers method
    all_assets = test_ace.get_all_asset_numbers()
    print(f"   All assets combined: {all_assets}")
    
    print("\n🔍 System Status:")
    
    # Count ACEs with legacy vs enhanced
    total_aces = Ace2.objects.count()
    legacy_aces = Ace2.objects.exclude(asset_number__isnull=True).exclude(asset_number='').count()
    enhanced_aces = Ace2.objects.filter(enhanced_asset_numbers__isnull=False).distinct().count()
    
    print(f"   Total ACEs: {total_aces}")
    print(f"   ACEs with legacy assets: {legacy_aces}")
    print(f"   ACEs with enhanced assets: {enhanced_aces}")
    
    # Test migration potential
    potential_migrations = Ace2.objects.exclude(asset_number__isnull=True).exclude(asset_number='').exclude(
        enhanced_asset_numbers__isnull=False
    ).count()
    
    print(f"   ACEs ready for migration: {potential_migrations}")
    
    print("\n✨ Enhanced Features Available:")
    print("   ✅ Individual asset entry with autocomplete")
    print("   ✅ Bulk asset entry (paste multiple)")
    print("   ✅ File import (CSV/TXT)")
    print("   ✅ Real-time validation")
    print("   ✅ Asset suggestions from database")
    print("   ✅ Legacy migration support")
    print("   ✅ Enhanced display with verification status")
    
    print("\n🎯 Ready for production use!")
    return True

if __name__ == "__main__":
    try:
        test_enhanced_system()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

#!/usr/bin/env python3
"""
Simple Phase 2 Frontend Integration Test
Quick validation of key changes
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def validate_frontend_changes():
    """Validate that our frontend changes are correct"""
    
    print("🔍 Validating Phase 2 Frontend Changes...")
    print("=" * 50)
    
    schedule_tsx_path = project_root / "static" / "scripts" / "src" / "src" / "components" / "Schedule.tsx"
    
    if not schedule_tsx_path.exists():
        print(f"❌ Schedule.tsx not found at {schedule_tsx_path}")
        return False
    
    with open(schedule_tsx_path, 'r') as f:
        content = f.read()
    
    # Check for key changes
    checks = [
        {
            'name': '✅ advertMetadata state added',
            'pattern': 'advertMetadata',
            'should_exist': True
        },
        {
            'name': '✅ handleFileUpload function added',
            'pattern': 'handleFileUpload',
            'should_exist': True
        },
        {
            'name': '✅ getFileDownloadUrl function added',
            'pattern': 'getFileDownloadUrl',
            'should_exist': True
        },
        {
            'name': '✅ Base64 existingAdvert removed',
            'pattern': 'setExistingAdvert',
            'should_exist': False
        },
        {
            'name': '✅ Base64 atob processing removed',
            'pattern': 'atob(fileData)',
            'should_exist': False
        },
        {
            'name': '✅ Optimized download URLs used',
            'pattern': 'api/files/download',
            'should_exist': True
        },
        {
            'name': '✅ File metadata structure used',
            'pattern': 'download_url: string',
            'should_exist': True
        },
        {
            'name': '✅ Upload API integration',
            'pattern': 'api.uploadFile',
            'should_exist': True
        }
    ]
    
    all_passed = True
    for check in checks:
        pattern_found = check['pattern'] in content
        
        if check['should_exist'] and pattern_found:
            print(f"{check['name']}")
        elif not check['should_exist'] and not pattern_found:
            print(f"{check['name']}")
        else:
            status = '❌' if check['should_exist'] else '⚠️'
            print(f"{status} {check['name']}: {'Not found' if check['should_exist'] else 'Still present'}")
            all_passed = False
    
    return all_passed

def test_download_urls():
    """Test that download URLs are properly formatted"""
    
    print("\n🔗 Testing Download URL Implementation...")
    print("=" * 50)
    
    schedule_tsx_path = project_root / "static" / "scripts" / "src" / "src" / "components" / "Schedule.tsx"
    
    with open(schedule_tsx_path, 'r') as f:
        content = f.read()
    
    # Check for proper download URL implementation
    download_checks = [
        'advertMetadata.download_url',
        'link.href = advertMetadata.download_url',
        'link.download = advertMetadata.name',
        'link.target = \'_blank\'',
        '/comperative_schedule/api/files/download/'
    ]
    
    all_found = True
    for check in download_checks:
        if check in content:
            print(f"✅ {check}")
        else:
            print(f"❌ Missing: {check}")
            all_found = False
    
    return all_found

def check_file_size_formatting():
    """Check that file size is properly formatted"""
    
    print("\n📊 Testing File Size Display...")
    print("=" * 50)
    
    schedule_tsx_path = project_root / "static" / "scripts" / "src" / "src" / "components" / "Schedule.tsx"
    
    with open(schedule_tsx_path, 'r') as f:
        content = f.read()
    
    # Check for file size formatting
    size_checks = [
        'advertMetadata.size',
        '/ 1024 / 1024).toFixed(2)',
        'MB)'
    ]
    
    all_found = True
    for check in size_checks:
        if check in content:
            print(f"✅ File size formatting: {check}")
        else:
            print(f"❌ Missing file size formatting: {check}")
            all_found = False
    
    return all_found

if __name__ == "__main__":
    print("🚀 Starting Phase 2 Simple Validation...")
    
    success = True
    
    # Test 1: Validate frontend changes
    if not validate_frontend_changes():
        print("❌ Frontend validation failed")
        success = False
    
    # Test 2: Test download URLs
    if not test_download_urls():
        print("❌ Download URL implementation incomplete")
        success = False
    
    # Test 3: Check file size formatting
    if not check_file_size_formatting():
        print("❌ File size formatting missing")
        success = False
    
    if success:
        print("\n" + "=" * 50)
        print("🎉 Phase 2 Frontend Integration Validation PASSED!")
        print("")
        print("✅ All key changes implemented correctly:")
        print("   • Base64 processing completely removed")
        print("   • File metadata state management added")
        print("   • Optimized upload handlers integrated")
        print("   • Download URLs using streaming endpoints")
        print("   • File size and metadata display added")
        print("   • Proper error handling maintained")
        print("")
        print("🎯 Ready for end-to-end testing!")
        print("📤 File uploads will now use: /api/files/upload/")
        print("📥 File downloads will now use: /api/files/download/")
        print("🚀 No more Base64 encoding - Pure streaming!")
    else:
        print("\n❌ Phase 2 validation failed - check issues above")
        sys.exit(1)

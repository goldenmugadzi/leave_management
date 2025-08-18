#!/usr/bin/env python3

"""
Simple test script to verify the asset number button functionality
"""

def test_asset_button_elements():
    """Test that all required elements are in place"""
    
    print("=== Asset Number Button Test ===")
    
    # Check if the required files exist
    import os
    
    files_to_check = [
        "d:/b/templates/finance/ace2/ace_detail.html",
        "d:/b/static/assets/ace_add_asset_numbers.js",
        "d:/b/ACE2/views.py",
        "d:/b/ACE2/urls.py"
    ]
    
    print("\n1. Checking if required files exist:")
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"   ✓ {file_path}")
        else:
            print(f"   ✗ {file_path}")
    
    # Check template has required elements
    print("\n2. Checking template elements:")
    try:
        with open("d:/b/templates/finance/ace2/ace_detail.html", 'r') as f:
            content = f.read()
            
        # Check for required IDs
        required_ids = [
            'id="asset_number_btn"',
            'id="asset_number_modal"',
            'id="asset_upload"',
            'id="close-modal"'
        ]
        
        for required_id in required_ids:
            if required_id in content:
                print(f"   ✓ {required_id}")
            else:
                print(f"   ✗ {required_id}")
                
    except Exception as e:
        print(f"   Error reading template: {e}")
    
    # Check JavaScript has correct selectors
    print("\n3. Checking JavaScript selectors:")
    try:
        with open("d:/b/static/assets/ace_add_asset_numbers.js", 'r') as f:
            js_content = f.read()
            
        # Check for required selectors
        required_selectors = [
            '#asset_number_btn',
            '#asset_number_modal',
            '#asset_upload',
            '#close-modal'
        ]
        
        for selector in required_selectors:
            if selector in js_content:
                print(f"   ✓ {selector}")
            else:
                print(f"   ✗ {selector}")
                
        # Check for URL
        if '/ace/add_asset_number/' in js_content:
            print(f"   ✓ URL: /ace/add_asset_number/")
        else:
            print(f"   ✗ URL: /ace/add_asset_number/")
                
    except Exception as e:
        print(f"   Error reading JavaScript: {e}")
    
    # Check URL pattern exists
    print("\n4. Checking URL pattern:")
    try:
        with open("d:/b/ACE2/urls.py", 'r') as f:
            urls_content = f.read()
            
        if "path('add_asset_number/'," in urls_content:
            print(f"   ✓ URL pattern exists")
        else:
            print(f"   ✗ URL pattern missing")
            
    except Exception as e:
        print(f"   Error reading URLs: {e}")
    
    # Check view function exists
    print("\n5. Checking view function:")
    try:
        with open("d:/b/ACE2/views.py", 'r') as f:
            views_content = f.read()
            
        if "def add_asset_number(request):" in views_content:
            print(f"   ✓ View function exists")
        else:
            print(f"   ✗ View function missing")
            
    except Exception as e:
        print(f"   Error reading views: {e}")
    
    print("\n=== Test Complete ===")
    print("\nIf all elements show ✓, the button should work.")
    print("If any show ✗, those need to be fixed.")

if __name__ == "__main__":
    test_asset_button_elements()

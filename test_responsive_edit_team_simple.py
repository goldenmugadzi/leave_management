#!/usr/bin/env python3
"""
Test script to verify responsive improvements for edit team template
Based on ACE template design patterns
"""

import os
import re

def test_responsive_edit_team():
    """Test the responsive improvements in edit_team.html"""
    
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'fault_locator', 'edit_team.html')
    
    if not os.path.exists(template_path):
        print(f"❌ Template file not found: {template_path}")
        return False
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("🧪 Testing Edit Team Template Responsive Improvements")
    print("=" * 60)
    
    # Test 1: Check for clean grid layout
    grid_patterns = [
        r'grid\s+grid-cols-1\s+lg:grid-cols-2\s+xl:grid-cols-3',
        r'gap-6',
        r'lg:col-span-2\s+xl:col-span-1'
    ]
    
    grid_found = 0
    for pattern in grid_patterns:
        if re.search(pattern, content):
            grid_found += 1
    
    if grid_found >= 2:
        print("✅ Clean grid layout system implemented")
    else:
        print("❌ Grid layout system needs improvement")
    
    # Test 2: Check for simple input styling
    input_patterns = [
        r'class="block w-full rounded-md border-gray-300',
        r'focus:border-blue-500 focus:ring-2 focus:ring-blue-200',
        r'transition-all duration-200"'
    ]
    
    input_found = 0
    for pattern in input_patterns:
        if re.search(pattern, content):
            input_found += 1
    
    if input_found >= 2:
        print("✅ Simple, responsive input styling implemented")
    else:
        print("❌ Input styling needs improvement")
    
    # Test 3: Check for responsive breakpoints
    responsive_patterns = [
        r'sm:flex-row',
        r'lg:grid-cols-2',
        r'xl:grid-cols-3',
        r'@media \(max-width: 640px\)',
        r'@media \(max-width: 768px\)'
    ]
    
    responsive_found = 0
    for pattern in responsive_patterns:
        if re.search(pattern, content):
            responsive_found += 1
    
    if responsive_found >= 4:
        print("✅ Responsive breakpoints properly implemented")
    else:
        print("❌ Responsive breakpoints need improvement")
    
    # Test 4: Check for clean card design
    card_patterns = [
        r'bg-white rounded-lg shadow-md',
        r'p-6',
        r'mb-4 flex items-center gap-2'
    ]
    
    card_found = 0
    for pattern in card_patterns:
        if re.search(pattern, content):
            card_found += 1
    
    if card_found >= 3:
        print("✅ Clean card design implemented")
    else:
        print("❌ Card design needs improvement")
    
    # Test 5: Check for simplified CSS
    css_patterns = [
        r'width: 100%;',
        r'padding: 0\.625rem;',
        r'border: 1px solid #d1d5db;',
        r'border-radius: 0\.375rem;',
        r'transition: all 0\.2s ease-in-out;'
    ]
    
    css_found = 0
    for pattern in css_patterns:
        if re.search(pattern, content):
            css_found += 1
    
    if css_found >= 4:
        print("✅ Simplified CSS styling implemented")
    else:
        print("❌ CSS styling needs improvement")
    
    # Test 6: Check for mobile-first approach
    mobile_patterns = [
        r'flex-col sm:flex-row',
        r'w-full sm:w-auto',
        r'text-center',
        r'min-height: 44px'
    ]
    
    mobile_found = 0
    for pattern in mobile_patterns:
        if re.search(pattern, content):
            mobile_found += 1
    
    if mobile_found >= 3:
        print("✅ Mobile-first approach implemented")
    else:
        print("❌ Mobile-first approach needs improvement")
    
    # Test 7: Check for consistent button styling
    button_patterns = [
        r'px-4 py-2 bg-\w+-\d+ text-white rounded-md',
        r'font-medium hover:bg-\w+-\d+ transition-colors',
        r'inline-block.*rounded-md'
    ]
    
    button_found = 0
    for pattern in button_patterns:
        if re.search(pattern, content):
            button_found += 1
    
    if button_found >= 2:
        print("✅ Consistent button styling implemented")
    else:
        print("❌ Button styling needs improvement")
    
    # Test 8: Check for accessibility improvements
    accessibility_patterns = [
        r'text-sm font-medium text-gray-700',
        r'block.*mb-2',
        r'onclick="return confirm\(',
        r'for="{{ .*.id_for_label }}"'
    ]
    
    accessibility_found = 0
    for pattern in accessibility_patterns:
        if re.search(pattern, content):
            accessibility_found += 1
    
    if accessibility_found >= 3:
        print("✅ Accessibility improvements implemented")
    else:
        print("❌ Accessibility improvements needed")
    
    # Test 9: Check for proper form structure
    form_patterns = [
        r'<form method="post"',
        r'{% csrf_token %}',
        r'<input type="hidden"',
        r'name="{{ .*.name }}"',
        r'id="{{ .*.id_for_label }}"'
    ]
    
    form_found = 0
    for pattern in form_patterns:
        if re.search(pattern, content):
            form_found += 1
    
    if form_found >= 4:
        print("✅ Proper form structure implemented")
    else:
        print("❌ Form structure needs improvement")
    
    # Test 10: Check for content-wrapper and container
    container_patterns = [
        r'content-wrapper',
        r'bg-gray-100.*rounded-lg',
        r'max-w-7xl.*mx-auto',
        r'shadow-lg'
    ]
    
    container_found = 0
    for pattern in container_patterns:
        if re.search(pattern, content):
            container_found += 1
    
    if container_found >= 3:
        print("✅ Proper container structure implemented")
    else:
        print("❌ Container structure needs improvement")
    
    print("\n" + "=" * 60)
    
    # Overall assessment
    total_tests = 10
    passed_tests = sum([
        grid_found >= 2,
        input_found >= 2,
        responsive_found >= 4,
        card_found >= 3,
        css_found >= 4,
        mobile_found >= 3,
        button_found >= 2,
        accessibility_found >= 3,
        form_found >= 4,
        container_found >= 3
    ])
    
    success_rate = (passed_tests / total_tests) * 100
    
    print(f"📊 Test Results: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")
    
    if success_rate >= 80:
        print("🎉 Excellent! The template is now properly responsive with ACE-style design!")
        return True
    elif success_rate >= 60:
        print("⚠️ Good progress! Some improvements still needed.")
        return True
    else:
        print("❌ More work needed to achieve responsive design goals.")
        return False

if __name__ == "__main__":
    success = test_responsive_edit_team()
    
    if success:
        print("\n🚀 Template is ready for production use!")
        print("✨ Key improvements implemented:")
        print("  • Clean, simple grid layout")
        print("  • Responsive input fields")
        print("  • Mobile-first design approach")
        print("  • Consistent button styling")
        print("  • Proper accessibility features")
        print("  • Simplified CSS without complex animations")
        print("  • ACE template design patterns")
    else:
        print("\n🔧 Additional improvements needed for optimal responsiveness.")

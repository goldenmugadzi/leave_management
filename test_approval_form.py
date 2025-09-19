#!/usr/bin/env python
"""
Test script to verify the ApprovalForm fixes for rejection validation.
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings')
sys.path.append(os.path.dirname(__file__))
django.setup()

from approve.forms import ApprovalForm

def test_approval_form_validation():
    """Test the ApprovalForm validation logic."""
    print("Testing ApprovalForm validation...")

    # Test 1: Valid approval without comment
    form_data = {'approved': 'Approved', 'comment': ''}
    form = ApprovalForm(data=form_data)
    is_valid = form.is_valid()
    print(f"✓ Test 1 - Valid approval without comment: {'PASS' if is_valid else 'FAIL'}")
    if not is_valid:
        print(f"  Errors: {form.errors}")

    # Test 2: Valid approval with comment
    form_data = {'approved': 'Approved', 'comment': 'Looks good!'}
    form = ApprovalForm(data=form_data)
    is_valid = form.is_valid()
    print(f"✓ Test 2 - Valid approval with comment: {'PASS' if is_valid else 'FAIL'}")
    if not is_valid:
        print(f"  Errors: {form.errors}")

    # Test 3: Valid rejection with comment
    form_data = {'approved': 'Rejected', 'comment': 'Insufficient budget allocation'}
    form = ApprovalForm(data=form_data)
    is_valid = form.is_valid()
    print(f"✓ Test 3 - Valid rejection with comment: {'PASS' if is_valid else 'FAIL'}")
    if not is_valid:
        print(f"  Errors: {form.errors}")

    # Test 4: Invalid rejection without comment (should fail)
    form_data = {'approved': 'Rejected', 'comment': ''}
    form = ApprovalForm(data=form_data)
    is_valid = form.is_valid()
    print(f"✓ Test 4 - Invalid rejection without comment: {'PASS' if not is_valid else 'FAIL'}")
    if not is_valid:
        print(f"  Expected error: {form.errors}")
    else:
        print("  ERROR: Form should have failed validation!")

    # Test 5: Invalid rejection with whitespace-only comment (should fail)
    form_data = {'approved': 'Rejected', 'comment': '   '}
    form = ApprovalForm(data=form_data)
    is_valid = form.is_valid()
    print(f"✓ Test 5 - Invalid rejection with whitespace comment: {'PASS' if not is_valid else 'FAIL'}")
    if not is_valid:
        print(f"  Expected error: {form.errors}")
    else:
        print("  ERROR: Form should have failed validation!")

    print("\nForm validation tests completed!")

if __name__ == '__main__':
    test_approval_form_validation()
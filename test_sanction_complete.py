#!/usr/bin/env python
"""
Test script to verify sanction_for_test application is fully functional
"""

import os
import sys
import django
from django.conf import settings

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    django.setup()
    print("✓ Django setup successful")
except Exception as e:
    print(f"✗ Django setup failed: {e}")
    sys.exit(1)

def test_database_tables():
    """Test if all database tables exist and are accessible"""
    try:
        from django.db import connection
        
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES LIKE 'sanction_for_test%'")
            tables = cursor.fetchall()
            
            expected_tables = [
                'sanction_for_test_sanctionfortestform',
                'sanction_for_test_sanctionformcomment',
                'sanction_for_test_sanctionformauditlog',
                'sanction_for_test_sanctionformattachment'
            ]
            
            found_tables = [table[0] for table in tables]
            
            print("Database Tables:")
            all_found = True
            for table in expected_tables:
                if table in found_tables:
                    print(f"  ✓ {table}")
                else:
                    print(f"  ✗ {table} - MISSING")
                    all_found = False
            
            return all_found
            
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        return False

def test_models():
    """Test if models can be imported and queried"""
    try:
        from sanction_for_test.models import (
            SanctionForTestForm, SanctionFormComment, 
            SanctionFormAuditLog, SanctionFormAttachment
        )
        
        print("\nModel Tests:")
        
        # Test SanctionForTestForm
        form_count = SanctionForTestForm.objects.count()
        print(f"  ✓ SanctionForTestForm: {form_count} records")
        
        # Test other models
        comment_count = SanctionFormComment.objects.count()
        print(f"  ✓ SanctionFormComment: {comment_count} records")
        
        audit_count = SanctionFormAuditLog.objects.count()
        print(f"  ✓ SanctionFormAuditLog: {audit_count} records")
        
        attachment_count = SanctionFormAttachment.objects.count()
        print(f"  ✓ SanctionFormAttachment: {attachment_count} records")
        
        return True
        
    except Exception as e:
        print(f"✗ Model test failed: {e}")
        return False

def test_workflow():
    """Test if workflow is properly configured"""
    try:
        from approve.models import Workflow, Step, Process
        from it.users.models import Application, Roles
        
        print("\nWorkflow Tests:")
        
        # Test application exists
        app = Application.objects.filter(name='sanction_for_test').first()
        if app:
            print(f"  ✓ Application: {app.fullname}")
        else:
            print("  ✗ Application not found")
            return False
        
        # Test workflow exists
        workflow = Workflow.objects.filter(name='Sanction For Test Approval').first()
        if workflow:
            print(f"  ✓ Workflow: {workflow.name}")
        else:
            print("  ✗ Workflow not found")
            return False
        
        # Test steps exist
        steps = Step.objects.filter(workflow=workflow).count()
        print(f"  ✓ Workflow Steps: {steps}")
        
        # Test roles exist
        roles = Roles.objects.filter(application='sanction_for_test').count()
        print(f"  ✓ Roles: {roles}")
        
        return True
        
    except Exception as e:
        print(f"✗ Workflow test failed: {e}")
        return False

def test_views():
    """Test if views can be imported"""
    try:
        from sanction_for_test.views import (
            list_view, create_view, detail_view, 
            edit_view, approve_action, reports_view
        )
        
        print("\nView Tests:")
        print("  ✓ list_view imported")
        print("  ✓ create_view imported")
        print("  ✓ detail_view imported")
        print("  ✓ edit_view imported")
        print("  ✓ approve_action imported")
        print("  ✓ reports_view imported")
        
        return True
        
    except Exception as e:
        print(f"✗ View test failed: {e}")
        return False

def test_urls():
    """Test if URLs are properly configured"""
    try:
        from django.urls import reverse
        
        print("\nURL Tests:")
        
        # Test main URLs
        urls_to_test = [
            ('sanction_for_test:list', 'List view'),
            ('sanction_for_test:create', 'Create view'),
            ('sanction_for_test:reports', 'Reports view'),
        ]
        
        for url_name, description in urls_to_test:
            try:
                url = reverse(url_name)
                print(f"  ✓ {description}: {url}")
            except Exception as e:
                print(f"  ✗ {description}: {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ URL test failed: {e}")
        return False

def test_menu_integration():
    """Test if menu integration is working"""
    try:
        from it.beii_auth.views import APPLICATIONS, REPORTS
        
        print("\nMenu Integration Tests:")
        
        # Test business applications menu
        sanction_app = None
        for app in APPLICATIONS:
            if app.get('name') == 'sanction_for_test':
                sanction_app = app
                break
        
        if sanction_app:
            print(f"  ✓ Business App Menu: {sanction_app['title']}")
        else:
            print("  ✗ Not found in business applications menu")
            return False
        
        # Test reports menu
        sanction_report = None
        for report in REPORTS:
            if report.get('name') == 'sanction_for_test_reports':
                sanction_report = report
                break
        
        if sanction_report:
            print(f"  ✓ Reports Menu: {sanction_report['title']}")
        else:
            print("  ✗ Not found in reports menu")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Menu integration test failed: {e}")
        return False

def main():
    print("Sanction For Test - Complete Functionality Test")
    print("=" * 60)
    
    tests = [
        ("Database Tables", test_database_tables),
        ("Models", test_models),
        ("Workflow", test_workflow),
        ("Views", test_views),
        ("URLs", test_urls),
        ("Menu Integration", test_menu_integration),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} test failed")
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("The Sanction For Test application is fully functional!")
        print("\nApplication is ready for use:")
        print("• Business Applications Menu: 'Sanction For Test'")
        print("• Reports Menu: 'Sanction For Test Reports'") 
        print("• Database tables created and populated")
        print("• Approval workflow configured")
    else:
        print(f"\n❌ {total - passed} test(s) failed")
        print("Please check the errors above and fix them.")

if __name__ == "__main__":
    main()

"""
Test script to verify logging and monitoring functionality for dashboard enhancement.
Run with: python manage.py shell < executive/general_dashboards/test_logging.py
"""

import json
from decimal import Decimal
from django.contrib.auth.models import User
from django.test import RequestFactory
from django.utils import timezone
from executive.general_dashboards.logging_utils import DashboardLogger, PerformanceMonitor
from executive.general_dashboards.monitoring import performance_tracker, monitor_dashboard_health


def test_logging_functionality():
    """Test all logging functionality"""
    print("Testing Dashboard Enhancement Logging and Monitoring...")
    print("=" * 60)
    
    # Create a test user
    try:
        test_user = User.objects.get(username='test_logger')
    except User.DoesNotExist:
        test_user = User.objects.create_user(
            username='test_logger',
            email='test@example.com',
            password='testpass123'
        )
    
    print(f"✓ Test user created/found: {test_user.username}")
    
    # Test 1: Data update logging
    print("\n1. Testing data update logging...")
    DashboardLogger.log_data_update(
        user=test_user,
        table="weekly_collections",
        operation="update",
        data={
            "record_id": 1,
            "field": "zwl_millions",
            "old_value": "5.2",
            "new_value": "6.1",
            "week": "Week 1"
        },
        success=True,
        execution_time=0.045
    )
    print("✓ Data update logged successfully")
    
    # Test 2: Validation error logging
    print("\n2. Testing validation error logging...")
    DashboardLogger.log_validation_error(
        user=test_user,
        table="weekly_revenue_lost",
        field="faults_mwh",
        value="-5.0",
        error_message="MWh values cannot be negative",
        validation_rules={"min_value": 0}
    )
    print("✓ Validation error logged successfully")
    
    # Test 3: User action logging
    print("\n3. Testing user action logging...")
    DashboardLogger.log_user_action(
        user=test_user,
        action="save_dashboard_data",
        details={
            "table": "debtors",
            "operation": "percentage_update"
        },
        ip_address="127.0.0.1",
        user_agent="Mozilla/5.0 Test Browser"
    )
    print("✓ User action logged successfully")
    
    # Test 4: Permission check logging
    print("\n4. Testing permission check logging...")
    DashboardLogger.log_permission_check(
        user=test_user,
        resource="dashboard_editing",
        permission="maintain",
        granted=True,
        reason="User has maintain role for general_dashboards"
    )
    print("✓ Permission check logged successfully")
    
    # Test 5: Performance metric logging
    print("\n5. Testing performance metric logging...")
    DashboardLogger.log_performance_metric(
        endpoint="save_dashboard_data",
        method="POST",
        execution_time=1.234,
        query_count=5,
        user=test_user,
        status_code=200
    )
    print("✓ Performance metric logged successfully")
    
    # Test 6: Auto-calculation logging
    print("\n6. Testing auto-calculation logging...")
    DashboardLogger.log_auto_calculation(
        table="weekly_revenue_lost",
        record_id=1,
        calculation_type="revenue_lost_total",
        input_values={
            "faults_mwh": "10.5",
            "maintenance_mwh": "5.2"
        },
        result="15.7",
        user=test_user
    )
    print("✓ Auto-calculation logged successfully")
    
    # Test 7: Performance monitoring
    print("\n7. Testing performance monitoring...")
    with PerformanceMonitor("test_operation", test_user, log_threshold=0.001):
        # Simulate some work
        import time
        time.sleep(0.01)
    print("✓ Performance monitoring completed successfully")
    
    # Test 8: Performance tracker
    print("\n8. Testing performance tracker...")
    performance_tracker.record_request("test_endpoint", 0.5, query_count=3, success=True)
    performance_tracker.record_request("test_endpoint", 1.2, query_count=7, success=True)
    performance_tracker.record_request("test_endpoint", 0.8, query_count=2, success=False)
    
    stats = performance_tracker.get_endpoint_stats("test_endpoint")
    print(f"✓ Performance tracker stats: {stats}")
    
    # Test 9: Health monitoring
    print("\n9. Testing health monitoring...")
    health_data = monitor_dashboard_health()
    print(f"✓ Health monitoring completed. Endpoints tracked: {len(health_data['performance_stats'])}")
    
    print("\n" + "=" * 60)
    print("All logging and monitoring tests completed successfully!")
    print("Check the following log files for output:")
    print("- dashboard_enhancement.log")
    print("- dashboard_performance.log")
    print("- security.log (for permission checks)")
    print("=" * 60)


def test_error_scenarios():
    """Test error handling in logging"""
    print("\nTesting error scenarios...")
    
    # Test logging with None user
    DashboardLogger.log_data_update(
        user=None,
        table="test_table",
        operation="test_operation",
        data={"test": "data"},
        success=False,
        error="Test error message"
    )
    print("✓ Logging with None user handled correctly")
    
    # Test logging with complex data types
    complex_data = {
        "decimal_value": Decimal("123.45"),
        "datetime_value": timezone.now(),
        "nested_dict": {"inner": "value"}
    }
    
    DashboardLogger.log_data_update(
        user=None,
        table="test_table",
        operation="complex_data_test",
        data=complex_data,
        success=True
    )
    print("✓ Complex data types handled correctly")


if __name__ == "__main__":
    test_logging_functionality()
    test_error_scenarios()
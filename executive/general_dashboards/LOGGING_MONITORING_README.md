# Dashboard Enhancement Logging and Monitoring

This document describes the comprehensive logging and monitoring implementation for the dashboard enhancement feature.

## Overview

The logging and monitoring system provides:
- **Structured logging** for all data operations
- **Performance monitoring** for API endpoints
- **User action tracking** for audit trails
- **Validation error logging** for debugging
- **System health monitoring** for operational insights

## Components

### 1. Logging Utilities (`logging_utils.py`)

#### DashboardLogger Class
Centralized logging utility with methods for:
- `log_data_update()` - Log data modification operations
- `log_validation_error()` - Log validation failures
- `log_user_action()` - Log user actions for audit trail
- `log_permission_check()` - Log permission checks for security
- `log_performance_metric()` - Log API performance metrics
- `log_auto_calculation()` - Log automatic calculations

#### Decorators
- `@log_api_performance()` - Automatically log API endpoint performance
- `@log_data_operation()` - Automatically log data operations

#### PerformanceMonitor Context Manager
```python
with PerformanceMonitor("operation_name", user):
    # Your code here
    pass
```

### 2. Performance Monitoring (`monitoring.py`)

#### PerformanceTracker Class
- Thread-safe metrics collection
- Response time tracking
- Query count monitoring
- Error rate calculation
- Endpoint statistics

#### DatabaseQueryMonitor Class
- Query performance analysis
- Slow query detection
- Query pattern analysis

#### SystemMetricsCollector Class
- Memory usage monitoring
- CPU usage tracking
- System health checks

#### AlertManager Class
- Performance threshold monitoring
- Automated alert generation
- Alert cooldown management

### 3. Monitoring Views (`monitoring_views.py`)

API endpoints for monitoring:
- `/monitoring/` - Main monitoring dashboard
- `/monitoring/api/performance/` - Performance statistics
- `/monitoring/api/health/` - System health data
- `/monitoring/api/queries/` - Database query performance
- `/monitoring/status/` - Simple health check

### 4. Management Commands

#### Performance Report Command
```bash
python manage.py dashboard_performance_report --format json --output report.json
```

Options:
- `--format` - Output format (json/text)
- `--output` - Output file path
- `--reset` - Reset metrics after report
- `--threshold` - Response time threshold

## Configuration

### Django Settings (`settings.py`)

The logging configuration includes:
- **dashboard_enhancement** logger - General dashboard operations
- **dashboard_performance** logger - Performance metrics
- **dashboard_security** logger - Security events

Log files:
- `dashboard_enhancement.log` - Main operations log
- `dashboard_performance.log` - Performance metrics log
- `security.log` - Security events log

### Environment Variables

Configure log file paths:
```bash
DASHBOARD_LOG_FILE=dashboard_enhancement.log
PERFORMANCE_LOG_FILE=dashboard_performance.log
SECURITY_LOG_FILE=security.log
```

## Usage Examples

### 1. Logging Data Updates

```python
from executive.general_dashboards.logging_utils import DashboardLogger

DashboardLogger.log_data_update(
    user=request.user,
    table="weekly_collections",
    operation="update",
    data={
        "record_id": 1,
        "field": "zwl_millions",
        "old_value": "5.2",
        "new_value": "6.1"
    },
    success=True,
    execution_time=0.045
)
```

### 2. Logging Validation Errors

```python
DashboardLogger.log_validation_error(
    user=request.user,
    table="weekly_revenue_lost",
    field="faults_mwh",
    value="-5.0",
    error_message="MWh values cannot be negative",
    validation_rules={"min_value": 0}
)
```

### 3. Performance Monitoring

```python
from executive.general_dashboards.logging_utils import log_api_performance

@log_api_performance("my_endpoint")
def my_view(request):
    # Your view code
    return JsonResponse({"success": True})
```

### 4. Performance Tracking

```python
from executive.general_dashboards.monitoring import performance_tracker

# Record a request
performance_tracker.record_request("endpoint_name", 1.5, query_count=5, success=True)

# Get statistics
stats = performance_tracker.get_endpoint_stats("endpoint_name")
```

## Log Format

### Data Update Logs
```
2025-08-27 14:31:04,657 [INFO] dashboard_enhancement: Data update successful
```

### Validation Error Logs
```
2025-08-27 14:31:04,657 [WARNING] dashboard_enhancement: Validation error in weekly_revenue_lost.faults_mwh
```

### Performance Logs
```
2025-08-27 14:31:04,667 [INFO] dashboard_enhancement: Performance: test_operation completed in 0.010s
```

## Monitoring Dashboard

Access the monitoring dashboard at `/executive/general_dashboards/monitoring/`

Features:
- Real-time performance statistics
- Slow endpoint identification
- System health metrics
- Error rate monitoring
- Query performance analysis

## API Endpoints

### Get Performance Stats
```
GET /executive/general_dashboards/monitoring/api/performance/
GET /executive/general_dashboards/monitoring/api/performance/?endpoint=save_dashboard_data
```

### System Health Check
```
GET /executive/general_dashboards/monitoring/api/health/
```

### Reset Performance Metrics
```
POST /executive/general_dashboards/monitoring/api/reset/
Content-Type: application/json
{"endpoint": "save_dashboard_data"}  // Optional: reset specific endpoint
```

## Testing

Run the logging test:
```python
python manage.py shell < executive/general_dashboards/test_logging.py
```

Generate performance report:
```bash
python manage.py dashboard_performance_report
```

## Security Considerations

- All user actions are logged with IP addresses and user agents
- Permission checks are logged for security monitoring
- Sensitive data is sanitized before logging
- Log files should be secured with appropriate file permissions

## Performance Impact

- Logging operations are designed to be lightweight
- Performance monitoring uses thread-safe data structures
- Log files use rotation to prevent unlimited growth
- Database query monitoring has minimal overhead

## Troubleshooting

### Common Issues

1. **Log files not created**: Check file permissions and LOG_FILE environment variables
2. **Performance data missing**: Ensure decorators are applied to view functions
3. **High memory usage**: Check log file rotation settings

### Debug Mode

Enable debug logging by setting the logger level to DEBUG:
```python
import logging
logging.getLogger('dashboard_enhancement').setLevel(logging.DEBUG)
```

## Integration with Existing Code

The logging and monitoring system is integrated into:
- `save_dashboard_data()` - Comprehensive data update logging
- `get_regions()` - User action and performance logging
- `dashboard_filter()` - Filter operation logging
- `user_permissions()` - Permission check logging

All new dashboard API endpoints include:
- Performance monitoring decorators
- User action logging
- Error handling with logging
- Validation error logging

## Future Enhancements

Potential improvements:
- Real-time alerting via email/Slack
- Grafana/Prometheus integration
- Log aggregation with ELK stack
- Machine learning for anomaly detection
- Custom dashboard widgets for monitoring
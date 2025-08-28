"""
Django management command to generate dashboard performance reports.
Usage: python manage.py dashboard_performance_report [--format json|text] [--output filename]
"""

import json
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from executive.general_dashboards.monitoring import (
    performance_tracker, monitor_dashboard_health, log_performance_summary
)
from executive.general_dashboards.logging_utils import dashboard_logger


class Command(BaseCommand):
    help = 'Generate dashboard performance report'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--format',
            choices=['json', 'text'],
            default='text',
            help='Output format (default: text)'
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Output file path (default: stdout)'
        )
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset performance metrics after generating report'
        )
        parser.add_argument(
            '--threshold',
            type=float,
            default=2.0,
            help='Response time threshold for slow endpoints (default: 2.0 seconds)'
        )
    
    def handle(self, *args, **options):
        try:
            # Generate comprehensive health report
            health_data = monitor_dashboard_health()
            
            # Get performance statistics
            all_stats = performance_tracker.get_all_stats()
            slow_endpoints = performance_tracker.get_slow_endpoints(options['threshold'])
            
            # Prepare report data
            report_data = {
                'generated_at': timezone.now().isoformat(),
                'summary': {
                    'total_endpoints': len(all_stats),
                    'total_requests': sum(s['total_requests'] for s in all_stats),
                    'slow_endpoints_count': len(slow_endpoints),
                    'avg_response_time': self._calculate_weighted_average(all_stats, 'avg_response_time'),
                    'avg_error_rate': self._calculate_weighted_average(all_stats, 'error_rate')
                },
                'endpoint_performance': all_stats,
                'slow_endpoints': slow_endpoints,
                'health_data': health_data
            }
            
            # Format and output report
            if options['format'] == 'json':
                output = json.dumps(report_data, indent=2, default=str)
            else:
                output = self._format_text_report(report_data)
            
            # Write to file or stdout
            if options['output']:
                with open(options['output'], 'w') as f:
                    f.write(output)
                self.stdout.write(
                    self.style.SUCCESS(f'Report written to {options["output"]}')
                )
            else:
                self.stdout.write(output)
            
            # Log the report generation
            dashboard_logger.info(
                "Performance report generated",
                extra={
                    'format': options['format'],
                    'output_file': options['output'],
                    'endpoints_analyzed': len(all_stats),
                    'slow_endpoints': len(slow_endpoints)
                }
            )
            
            # Reset metrics if requested
            if options['reset']:
                performance_tracker.reset_metrics()
                self.stdout.write(
                    self.style.WARNING('Performance metrics have been reset')
                )
                dashboard_logger.info("Performance metrics reset via management command")
            
            # Log summary
            log_performance_summary()
            
        except Exception as e:
            dashboard_logger.error(
                f"Error generating performance report: {str(e)}",
                exc_info=True
            )
            raise CommandError(f'Error generating report: {str(e)}')
    
    def _calculate_weighted_average(self, stats, field):
        """Calculate weighted average based on request count"""
        if not stats:
            return 0
        
        total_requests = sum(s['total_requests'] for s in stats)
        if total_requests == 0:
            return 0
        
        weighted_sum = sum(s[field] * s['total_requests'] for s in stats)
        return weighted_sum / total_requests
    
    def _format_text_report(self, data):
        """Format report data as human-readable text"""
        lines = []
        lines.append("=" * 60)
        lines.append("DASHBOARD PERFORMANCE REPORT")
        lines.append("=" * 60)
        lines.append(f"Generated at: {data['generated_at']}")
        lines.append("")
        
        # Summary section
        summary = data['summary']
        lines.append("SUMMARY")
        lines.append("-" * 20)
        lines.append(f"Total Endpoints: {summary['total_endpoints']}")
        lines.append(f"Total Requests: {summary['total_requests']}")
        lines.append(f"Slow Endpoints: {summary['slow_endpoints_count']}")
        lines.append(f"Average Response Time: {summary['avg_response_time']:.3f}s")
        lines.append(f"Average Error Rate: {summary['avg_error_rate']:.2f}%")
        lines.append("")
        
        # Endpoint performance section
        if data['endpoint_performance']:
            lines.append("ENDPOINT PERFORMANCE")
            lines.append("-" * 30)
            lines.append(f"{'Endpoint':<30} {'Requests':<10} {'Avg Time':<10} {'Error Rate':<12} {'Queries':<8}")
            lines.append("-" * 80)
            
            for stats in sorted(data['endpoint_performance'], 
                              key=lambda x: x['avg_response_time'], reverse=True):
                lines.append(
                    f"{stats['endpoint']:<30} "
                    f"{stats['total_requests']:<10} "
                    f"{stats['avg_response_time']:.3f}s{'':<4} "
                    f"{stats['error_rate']:.2f}%{'':<7} "
                    f"{stats['avg_query_count']:.1f}"
                )
            lines.append("")
        
        # Slow endpoints section
        if data['slow_endpoints']:
            lines.append("SLOW ENDPOINTS (ATTENTION REQUIRED)")
            lines.append("-" * 40)
            for stats in data['slow_endpoints']:
                lines.append(f"• {stats['endpoint']}")
                lines.append(f"  Average Response Time: {stats['avg_response_time']:.3f}s")
                lines.append(f"  Max Response Time: {stats['max_response_time']:.3f}s")
                lines.append(f"  Total Requests: {stats['total_requests']}")
                lines.append(f"  Error Rate: {stats['error_rate']:.2f}%")
                lines.append("")
        
        # System metrics section
        health = data['health_data']
        if 'system_metrics' in health:
            lines.append("SYSTEM METRICS")
            lines.append("-" * 20)
            
            memory = health['system_metrics']['memory']
            if 'error' not in memory:
                lines.append(f"Memory Usage: {memory.get('memory_percent', 'N/A')}%")
            
            cpu = health['system_metrics']['cpu']
            if 'error' not in cpu:
                lines.append(f"CPU Usage: {cpu.get('cpu_percent', 'N/A')}%")
                lines.append(f"CPU Cores: {cpu.get('cpu_count', 'N/A')}")
            lines.append("")
        
        # Query analysis section
        if 'query_analysis' in health and health['query_analysis']:
            lines.append("DATABASE QUERY ANALYSIS")
            lines.append("-" * 30)
            for query_type, analysis in health['query_analysis'].items():
                lines.append(f"{query_type} Queries:")
                lines.append(f"  Count: {analysis['count']}")
                lines.append(f"  Total Time: {analysis['total_time']:.3f}s")
                lines.append(f"  Average Time: {analysis['avg_time']:.3f}s")
                lines.append(f"  Max Time: {analysis['max_time']:.3f}s")
                lines.append("")
        
        lines.append("=" * 60)
        return "\n".join(lines)
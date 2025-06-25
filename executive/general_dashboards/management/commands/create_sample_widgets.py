from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from executive.general_dashboards.models import DashboardWidget, DashboardPreference
from it.users.models import Roles, Application

User = get_user_model()


class Command(BaseCommand):
    help = 'Create sample dashboard widgets and preferences'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating sample dashboard widgets...'))
        
        # Create sample widgets
        widgets_data = [
            {
                'name': 'pending_approvals',
                'title': 'Pending Approvals',
                'widget_type': 'card',
                'description': 'Shows count of pending approvals by type',
                'config': {
                    'chart_type': 'bar',
                    'show_trend': True,
                    'refresh_interval': 300
                }
            },
            {
                'name': 'approval_trends',
                'title': 'Approval Trends',
                'widget_type': 'chart',
                'description': 'Monthly approval trends chart',
                'config': {
                    'chart_type': 'line',
                    'time_period': '6_months',
                    'show_legend': True
                }
            },
            {
                'name': 'workload_distribution',
                'title': 'Workload Distribution',
                'widget_type': 'chart',
                'description': 'Distribution of workload across applications',
                'config': {
                    'chart_type': 'pie',
                    'show_percentages': True
                }
            },
            {
                'name': 'recent_actions',
                'title': 'Recent Actions',
                'widget_type': 'list',
                'description': 'List of recently completed actions',
                'config': {
                    'items_count': 10,
                    'show_timestamps': True
                }
            },
            {
                'name': 'performance_metrics',
                'title': 'Performance Metrics',
                'widget_type': 'metric',
                'description': 'Key performance indicators',
                'config': {
                    'metrics': ['avg_approval_time', 'approval_rate', 'backlog_count'],
                    'format': 'cards'
                }
            }
        ]
        
        created_count = 0
        for widget_data in widgets_data:
            widget, created = DashboardWidget.objects.get_or_create(
                name=widget_data['name'],
                defaults={
                    'title': widget_data['title'],
                    'widget_type': widget_data['widget_type'],
                    'description': widget_data['description'],
                    'config': widget_data['config']
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(f'Created widget: {widget.title}')
            else:
                self.stdout.write(f'Widget already exists: {widget.title}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} new widgets')
        )
        
        # Create default preferences for existing users without preferences
        users_without_prefs = User.objects.filter(dashboard_preferences__isnull=True)
        prefs_created = 0
        
        for user in users_without_prefs:
            try:
                DashboardPreference.objects.create(
                    user=user,
                    default_priority_filter='urgent',
                    items_per_page=10,
                    email_notifications=True
                )
                prefs_created += 1
                self.stdout.write(f'Created preferences for user: {user.username}')
            except Exception as e:
                self.stdout.write(f'Error creating preferences for {user.username}: {e}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Created default preferences for {prefs_created} users')
        ) 
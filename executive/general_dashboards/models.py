from django.db import models
from it.users.models import UserProfile, Roles, Application
from django.utils import timezone


class DashboardPreference(models.Model):
    """Store user dashboard preferences and settings"""
    user = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='dashboard_preferences')
    default_priority_filter = models.CharField(
        max_length=20, 
        choices=[('all', 'All'), ('urgent', 'Urgent'), ('high', 'High'), ('medium', 'Medium'), ('low', 'Low')],
        default='all'
    )
    items_per_page = models.IntegerField(default=10)
    show_completed_actions = models.BooleanField(default=False)
    email_notifications = models.BooleanField(default=True)
    dashboard_layout = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Dashboard preferences for {self.user.username}"


class ActionItemMetrics(models.Model):
    """Store metrics for action items to track performance"""
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    application = models.CharField(max_length=50)
    item_type = models.CharField(max_length=50)  # 'ace', 'pettycash', 'token', etc.
    item_id = models.CharField(max_length=100)
    action_taken = models.CharField(
        max_length=20,
        choices=[('approved', 'Approved'), ('rejected', 'Rejected'), ('forwarded', 'Forwarded')]
    )
    time_to_action = models.DurationField(help_text="Time from creation to action")
    action_date = models.DateTimeField(auto_now_add=True)
    comments = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-action_date']

    def __str__(self):
        return f"{self.user.username} {self.action_taken} {self.item_type} {self.item_id}"


class DashboardWidget(models.Model):
    """Define reusable dashboard widgets"""
    name = models.CharField(max_length=100, unique=True)
    title = models.CharField(max_length=200)
    widget_type = models.CharField(
        max_length=50,
        choices=[
            ('chart', 'Chart'),
            ('table', 'Table'),
            ('card', 'Card'),
            ('list', 'List'),
            ('metric', 'Metric')
        ]
    )
    description = models.TextField(blank=True)
    config = models.JSONField(default=dict, help_text="Widget configuration as JSON")
    required_roles = models.ManyToManyField(Roles, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class UserWidgetPreference(models.Model):
    """User-specific widget preferences"""
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    widget = models.ForeignKey(DashboardWidget, on_delete=models.CASCADE)
    position = models.IntegerField(default=0, help_text="Position on dashboard")
    is_visible = models.BooleanField(default=True)
    custom_config = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = ['user', 'widget']
        ordering = ['position']

    def __str__(self):
        return f"{self.user.username} - {self.widget.name}"

from django.db import models
from it.users.models import UserProfile, Roles, Application, Regions, Districts, Depots
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


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


class DashboardMetric(models.Model):
    """Store dashboard metric card data"""
    METRIC_TYPES = [
        ('energy_sold', 'Energy Sold'),
        ('growth', 'Growth'),
        ('revenue_usd', 'Revenue USD'),
        ('revenue_zwl', 'Revenue ZWL'),
        ('faults', 'Faults'),
        ('maintenance', 'Maintenance'),
    ]
    
    metric_type = models.CharField(max_length=20, choices=METRIC_TYPES, unique=True)
    value = models.CharField(max_length=50, help_text="Current value")
    unit = models.CharField(max_length=20, help_text="Unit of measurement")
    target = models.CharField(max_length=50, help_text="Target value")
    target_unit = models.CharField(max_length=20, help_text="Target unit")
    progress = models.FloatField(default=0, help_text="Progress percentage")
    
    # Location-based filtering
    region = models.ForeignKey('users.Regions', on_delete=models.CASCADE, null=True, blank=True)
    district = models.ForeignKey('users.Districts', on_delete=models.CASCADE, null=True, blank=True)
    depot = models.ForeignKey('users.Depots', on_delete=models.CASCADE, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True)

    class Meta:
        unique_together = ['metric_type', 'region', 'district', 'depot']

    def __str__(self):
        location = f" - {self.region or self.district or self.depot or 'Global'}"
        return f"{self.get_metric_type_display()}{location}"


class WeeklySales(models.Model):
    """Store weekly sales data"""
    week = models.CharField(max_length=20)
    zwl = models.CharField(max_length=50)
    usd = models.CharField(max_length=50)
    
    # Location-based filtering
    region = models.ForeignKey('users.Regions', on_delete=models.CASCADE, null=True, blank=True)
    district = models.ForeignKey('users.Districts', on_delete=models.CASCADE, null=True, blank=True)
    depot = models.ForeignKey('users.Depots', on_delete=models.CASCADE, null=True, blank=True)
    
    # Time tracking
    year = models.IntegerField(default=2024)
    week_number = models.IntegerField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['week_number', 'year', 'region', 'district', 'depot']
        ordering = ['week_number']

    def __str__(self):
        return f"{self.week} - {self.region or self.district or self.depot or 'Global'}"


class WeeklyOutage(models.Model):
    """Store weekly power outage data"""
    week = models.CharField(max_length=20)
    outages = models.IntegerField(default=0)
    resolved = models.IntegerField(default=0)
    pending = models.IntegerField(default=0)
    
    # Location-based filtering
    region = models.ForeignKey('users.Regions', on_delete=models.CASCADE, null=True, blank=True)
    district = models.ForeignKey('users.Districts', on_delete=models.CASCADE, null=True, blank=True)
    depot = models.ForeignKey('users.Depots', on_delete=models.CASCADE, null=True, blank=True)
    
    year = models.IntegerField(default=2024)
    week_number = models.IntegerField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['week_number', 'year', 'region', 'district', 'depot']
        ordering = ['week_number']

    def __str__(self):
        return f"{self.week} - {self.region or self.district or self.depot or 'Global'}"


class WeeklyFaultMaintenance(models.Model):
    """Store weekly faults and maintenance data"""
    week = models.CharField(max_length=20)
    faults = models.IntegerField(default=0)
    maintenance = models.IntegerField(default=0)
    completed = models.IntegerField(default=0)
    pending = models.IntegerField(default=0)
    
    # Location-based filtering
    region = models.ForeignKey('users.Regions', on_delete=models.CASCADE, null=True, blank=True)
    district = models.ForeignKey('users.Districts', on_delete=models.CASCADE, null=True, blank=True)
    depot = models.ForeignKey('users.Depots', on_delete=models.CASCADE, null=True, blank=True)
    
    year = models.IntegerField(default=2024)
    week_number = models.IntegerField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['week_number', 'year', 'region', 'district', 'depot']
        ordering = ['week_number']

    def __str__(self):
        return f"{self.week} - {self.region or self.district or self.depot or 'Global'}"


class TopDebtor(models.Model):
    """Store top debtors data"""
    name = models.CharField(max_length=200)
    amount = models.CharField(max_length=50)
    
    # Location-based filtering
    region = models.ForeignKey('users.Regions', on_delete=models.CASCADE, null=True, blank=True)
    district = models.ForeignKey('users.Districts', on_delete=models.CASCADE, null=True, blank=True)
    depot = models.ForeignKey('users.Depots', on_delete=models.CASCADE, null=True, blank=True)
    
    # Ranking
    rank = models.IntegerField(default=1)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['rank', 'region', 'district', 'depot']
        ordering = ['rank']

    def __str__(self):
        return f"{self.rank}. {self.name} - {self.amount}"


class WeeklyCollections(models.Model):
    """Store weekly collections data in ZWL and USD millions"""
    week = models.CharField(max_length=20, help_text="Week identifier (e.g., 'Week 1')")
    zwl_millions = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0)],
        help_text="Collections in ZWL millions"
    )
    usd_millions = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0)],
        help_text="Collections in USD millions"
    )
    
    # Location-based filtering (consistent with existing models)
    region = models.ForeignKey(Regions, on_delete=models.CASCADE, null=True, blank=True)
    district = models.ForeignKey(Districts, on_delete=models.CASCADE, null=True, blank=True)
    depot = models.ForeignKey(Depots, on_delete=models.CASCADE, null=True, blank=True)
    
    # Time tracking
    year = models.IntegerField(default=2025)
    week_number = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(53)])
    
    # Audit trail fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ['week_number', 'year', 'region', 'district', 'depot']
        ordering = ['week_number']
        verbose_name = "Weekly Collection"
        verbose_name_plural = "Weekly Collections"

    def __str__(self):
        location = self.region or self.district or self.depot or 'Global'
        return f"{self.week} - {location} (ZWL: {self.zwl_millions}M, USD: {self.usd_millions}M)"


class WeeklyRevenueLost(models.Model):
    """Store weekly revenue lost data due to faults and maintenance in MWh"""
    week = models.CharField(max_length=20, help_text="Week identifier (e.g., 'Week 1')")
    faults_mwh = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0)],
        help_text="Revenue lost due to faults in MWh"
    )
    maintenance_mwh = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0)],
        help_text="Revenue lost due to maintenance in MWh"
    )
    total_mwh = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0)],
        help_text="Total revenue lost in MWh (auto-calculated)"
    )
    
    # Location-based filtering (consistent with existing models)
    region = models.ForeignKey(Regions, on_delete=models.CASCADE, null=True, blank=True)
    district = models.ForeignKey(Districts, on_delete=models.CASCADE, null=True, blank=True)
    depot = models.ForeignKey(Depots, on_delete=models.CASCADE, null=True, blank=True)
    
    # Time tracking
    year = models.IntegerField(default=2025)
    week_number = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(53)])
    
    # Audit trail fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ['week_number', 'year', 'region', 'district', 'depot']
        ordering = ['week_number']
        verbose_name = "Weekly Revenue Lost"
        verbose_name_plural = "Weekly Revenue Lost"

    def save(self, *args, **kwargs):
        """Auto-calculate total MWh before saving"""
        self.total_mwh = self.faults_mwh + self.maintenance_mwh
        super().save(*args, **kwargs)

    def __str__(self):
        location = self.region or self.district or self.depot or 'Global'
        return f"{self.week} - {location} (Total: {self.total_mwh} MWh)"


class DebtorCategory(models.Model):
    """Store debtor category percentages by customer type"""
    CATEGORY_CHOICES = [
        ('mining', 'Mining'),
        ('domestic', 'Domestic'),
        ('industry', 'Industry'),
        ('commercial', 'Commercial'),
        ('farming', 'Farming'),
        ('government', 'Government'),
        ('parastatal', 'Parastatal'),
        ('local_authority', 'Local Authority'),
    ]
    
    category = models.CharField(
        max_length=20, 
        choices=CATEGORY_CHOICES,
        help_text="Customer category type"
    )
    percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0.00), MaxValueValidator(100.00)],
        help_text="Percentage of total debt (0.00 to 100.00)"
    )
    
    # Location-based filtering (consistent with existing models)
    region = models.ForeignKey(Regions, on_delete=models.CASCADE, null=True, blank=True)
    district = models.ForeignKey(Districts, on_delete=models.CASCADE, null=True, blank=True)
    depot = models.ForeignKey(Depots, on_delete=models.CASCADE, null=True, blank=True)
    
    # Time tracking for data relevance
    year = models.IntegerField(default=2025)
    month = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    
    # Audit trail fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ['category', 'year', 'month', 'region', 'district', 'depot']
        ordering = ['category']
        verbose_name = "Debtor Category"
        verbose_name_plural = "Debtor Categories"

    def __str__(self):
        location = self.region or self.district or self.depot or 'Global'
        return f"{self.get_category_display()} - {location} ({self.percentage}%)"

    def clean(self):
        """Validate that percentage is within valid range"""
        from django.core.exceptions import ValidationError
        
        if self.percentage < 0 or self.percentage > 100:
            raise ValidationError('Percentage must be between 0 and 100')
    
    def save(self, *args, **kwargs):
        """Override save to ensure data integrity"""
        self.full_clean()  # Run model validation
        super().save(*args, **kwargs)
    
    @classmethod
    def validate_percentages_sum_to_100(cls, categories_data, location_filters=None):
        """
        Validate that all category percentages for a location sum to 100%
        categories_data: list of dicts with 'category' and 'percentage' keys
        location_filters: dict with region, district, depot filters
        """
        total_percentage = sum(float(item['percentage']) for item in categories_data)
        if abs(total_percentage - 100.00) > 0.01:  # Allow small floating point differences
            raise ValueError(f"Category percentages must sum to 100%, got {total_percentage}%")
    
    @classmethod
    def auto_adjust_percentages(cls, location_filter, changed_category, new_percentage):
        """
        Auto-adjust other category percentages to maintain 100% total
        Returns dict of updated percentages for other categories
        """
        from decimal import Decimal
        
        # Get all categories for this location except the changed one
        other_categories = cls.objects.filter(
            **location_filter
        ).exclude(category=changed_category)
        
        new_percentage = Decimal(str(new_percentage))
        remaining_percentage = Decimal('100.00') - new_percentage
        updated_percentages = {}
        
        if other_categories.exists():
            # Calculate current total of other categories
            current_other_total = sum(cat.percentage for cat in other_categories)
            
            if current_other_total > 0:
                # Proportionally adjust other categories
                adjustment_factor = remaining_percentage / current_other_total
                
                for category in other_categories:
                    new_other_percentage = category.percentage * adjustment_factor
                    category.percentage = new_other_percentage.quantize(Decimal('0.01'))
                    category.save()
                    updated_percentages[category.category] = str(category.percentage)
            else:
                # If all other categories are 0, distribute remaining equally
                if remaining_percentage > 0 and len(other_categories) > 0:
                    equal_share = (remaining_percentage / len(other_categories)).quantize(Decimal('0.01'))
                    
                    for category in other_categories:
                        category.percentage = equal_share
                        category.save()
                        updated_percentages[category.category] = str(equal_share)
        
        return updated_percentages

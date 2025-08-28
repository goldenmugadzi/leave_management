from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from it.users.models import Regions, Districts, Depots, UserProfile


class WeeklyCollections(models.Model):
    """Weekly collections data in both ZWL and USD currencies"""
    
    week = models.CharField(max_length=20, help_text="Week identifier (e.g., 'Week 1', 'Week 2')")
    zwl_millions = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Collections in ZWL millions (e.g., 5.2 = 5.2 million ZWL)"
    )
    usd_millions = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Collections in USD millions (e.g., 5.2 = 5.2 million USD)"
    )
    
    # Location-based filtering (consistent with existing models)
    region = models.ForeignKey(
        Regions, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        help_text="Associated region for location-based filtering"
    )
    district = models.ForeignKey(
        Districts, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        help_text="Associated district for location-based filtering"
    )
    depot = models.ForeignKey(
        Depots, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        help_text="Associated depot for location-based filtering"
    )
    
    # Time tracking
    year = models.IntegerField(default=2025, help_text="Year for the weekly data")
    week_number = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(53)],
        help_text="Week number within the year (1-53)"
    )
    
        # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL, 
        null=True,
        help_text="User who last updated this record"
    )
    
    class Meta:
        db_table = 'general_dashboards_weeklycollections'
        verbose_name = 'Weekly Collections'
        verbose_name_plural = 'Weekly Collections'
        ordering = ['year', 'week_number']
        unique_together = ['year', 'week_number', 'region', 'district', 'depot']
        indexes = [
            models.Index(fields=['year', 'week_number']),
            models.Index(fields=['region', 'district', 'depot']),
        ]
    
    def __str__(self):
        location = self.get_location_display()
        return f"Week {self.week_number} ({self.year}) - {location} - ZWL: {self.zwl_millions}M, USD: {self.usd_millions}M"
    
    def get_location_display(self):
        """Get a human-readable location string"""
        if self.depot:
            return f"{self.depot.district.district} - {self.depot.depot}"
        elif self.district:
            return f"{self.district.region.region} - {self.district.district}"
        elif self.region:
            return self.region.region
        else:
            return "All Locations"


class WeeklyRevenueLost(models.Model):
    """Weekly revenue lost data categorized by faults and maintenance"""
    
    week = models.CharField(max_length=20, help_text="Week identifier (e.g., 'Week 1', 'Week 2')")
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
        help_text="Total revenue lost (auto-calculated: faults + maintenance)"
    )
    
    # Location and time fields (same pattern as WeeklyCollections)
    region = models.ForeignKey(
        Regions, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    district = models.ForeignKey(
        Districts, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    depot = models.ForeignKey(
        Depots, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    
    year = models.IntegerField(default=2025)
    week_number = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(53)]
    )
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        UserProfile, 
        on_delete=models.SET_NULL, 
        null=True
    )
    
    class Meta:
        db_table = 'general_dashboards_weeklyrevenuelost'
        verbose_name = 'Weekly Revenue Lost'
        verbose_name_plural = 'Weekly Revenue Lost'
        ordering = ['year', 'week_number']
        unique_together = ['year', 'week_number', 'region', 'district', 'depot']
        indexes = [
            models.Index(fields=['year', 'week_number']),
            models.Index(fields=['region', 'district', 'depot']),
        ]
    
    def __str__(self):
        location = self.get_location_display()
        return f"Week {self.week_number} ({self.year}) - {location} - Total: {self.total_mwh} MWh"
    
    def get_location_display(self):
        """Get a human-readable location string"""
        if self.depot:
            return f"{self.depot.district.district} - {self.depot.depot}"
        elif self.district:
            return f"{self.district.region.region} - {self.district.district}"
        elif self.region:
            return self.region.region
        else:
            return "All Locations"
    
    def save(self, *args, **kwargs):
        """Auto-calculate total MWh before saving"""
        if self.faults_mwh is not None and self.maintenance_mwh is not None:
            self.total_mwh = self.faults_mwh + self.maintenance_mwh
        super().save(*args, **kwargs)


class DebtorCategory(models.Model):
    """Debtor information categorized by customer type with percentage breakdowns"""
    
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
        unique=True,
        help_text="Customer category for debt classification"
    )
    percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Percentage of total debt for this category (0.00 to 100.00)"
    )
    
    # Location fields for location-based filtering
    region = models.ForeignKey(
        Regions, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    district = models.ForeignKey(
        Districts, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    depot = models.ForeignKey(
        Depots, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    
    # Time tracking
    year = models.IntegerField(default=2025)
    month = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        help_text="Month number (1-12)"
    )
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        UserProfile, 
        on_delete=models.SET_NULL, 
        null=True
    )
    
    class Meta:
        db_table = 'general_dashboards_debtorcategory'
        verbose_name = 'Debtor Category'
        verbose_name_plural = 'Debtor Categories'
        ordering = ['category']
        unique_together = ['category', 'year', 'month', 'region', 'district', 'depot']
        indexes = [
            models.Index(fields=['year', 'month']),
            models.Index(fields=['region', 'district', 'depot']),
        ]
    
    def __str__(self):
        location = self.get_location_display()
        return f"{self.get_category_display()} - {self.percentage}% - {location}"
    
    def get_location_display(self):
        """Get a human-readable location string"""
        if self.depot:
            return f"{self.depot.district.district} - {self.depot.depot}"
        elif self.district:
            return f"{self.district.region.region} - {self.district.district}"
        elif self.region:
            return self.region.region
        else:
            return "All Locations"
    
    def clean(self):
        """Validate that percentages sum to 100% for the same location and time period"""
        from django.core.exceptions import ValidationError
        
        # Get other categories for the same location and time period
        other_categories = DebtorCategory.objects.filter(
            year=self.year,
            month=self.month,
            region=self.region,
            district=self.district,
            depot=self.depot
        ).exclude(pk=self.pk)
        
        # Calculate total percentage including this category
        total_percentage = sum([cat.percentage for cat in other_categories]) + self.percentage
        
        if total_percentage > 100:
            raise ValidationError(
                f'Total percentage for this location and time period cannot exceed 100%. '
                f'Current total: {total_percentage}%'
            )

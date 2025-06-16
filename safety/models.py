from django.db import models
from it.users.models import *
from django.conf import settings

class SafetyMonthlyReport(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, blank=True, null=True)
    department = models.ForeignKey(Sections, on_delete=models.DO_NOTHING, blank=True, null=True)
    regions = models.ForeignKey(Regions, on_delete=models.DO_NOTHING, blank=True, null=True)
    # Date fields
    date = models.DateField(help_text="Any day in the month being reported")
    month = models.PositiveSmallIntegerField()
    year = models.PositiveSmallIntegerField()

    # Accident statistics
    work_related_accidents = models.PositiveIntegerField(default=0)
    disabling_accidents = models.PositiveIntegerField(default=0)
    fatal_accidents = models.PositiveIntegerField(default=0)
    man_hours_lost = models.PositiveIntegerField(default=0, help_text="Total man hours lost due to injury")
    accident_free_days = models.PositiveIntegerField(default=0)
    motor_vehicle_accidents = models.PositiveIntegerField(default=0)
    property_damaged = models.PositiveIntegerField(default=0)
    she_meetings_conducted = models.PositiveIntegerField(default=0)
    she_related_trainings = models.PositiveIntegerField(default=0)
    wellness_programmes = models.PositiveIntegerField(default=0)
    clear_up_campaigns = models.PositiveIntegerField(default=0)
    she_inspections_conducted = models.PositiveIntegerField(default=0)
    mock_drills_conducted = models.PositiveIntegerField(default=0)

    # Exposure
    number_of_workers = models.PositiveIntegerField(default=0)
    number_of_days = models.PositiveIntegerField(default=0)

    # Calculated rates (optional, can also be calculated on the fly)
    accident_frequency_rate = models.FloatField(default=0.0)
    injury_severity_rate = models.FloatField(default=0.0)

    # Year-to-date cumulative fields (optional, can be calculated in queries)
    ytd_work_related_accidents = models.PositiveIntegerField(default=0)
    ytd_disabling_accidents = models.PositiveIntegerField(default=0)
    ytd_fatal_accidents = models.PositiveIntegerField(default=0)
    ytd_man_hours_lost = models.PositiveIntegerField(default=0)
    ytd_accident_free_days = models.PositiveIntegerField(default=0)
    ytd_motor_vehicle_accidents = models.PositiveIntegerField(default=0)
    ytd_property_damaged = models.PositiveIntegerField(default=0)
    ytd_she_meetings_conducted = models.PositiveIntegerField(default=0)
    ytd_she_related_trainings = models.PositiveIntegerField(default=0)
    ytd_wellness_programmes = models.PositiveIntegerField(default=0)
    ytd_clear_up_campaigns = models.PositiveIntegerField(default=0)
    ytd_she_inspections_conducted = models.PositiveIntegerField(default=0)
    ytd_mock_drills_conducted = models.PositiveIntegerField(default=0)

    def save(self, *args, **kwargs):
        # Calculate rates before saving
        exposure_time = self.number_of_days * 7.5 * self.number_of_workers
        if exposure_time > 0:
            self.accident_frequency_rate = (self.work_related_accidents* 1_000_000 / exposure_time)
            self.injury_severity_rate = (self.man_hours_lost* 1_000_000 / exposure_time)
        else:
            self.accident_frequency_rate = 0
            self.injury_severity_rate = 0
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.year}-{self.month:02d} Safety Report"

from django.db import models
from it.users.models import *
from django.conf import settings

class SafetyMonthlyReport(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, blank=True, null=True)
    department = models.ForeignKey(Sections, on_delete=models.DO_NOTHING, blank=True, null=True)
    regions = models.ForeignKey(Regions, on_delete=models.DO_NOTHING, blank=True, null=True)
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

    
    accident_frequency_rate = models.FloatField(default=0.0)
    injury_severity_rate = models.FloatField(default=0.0)

<<<<<<< HEAD
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

    # Additional fields for detailed accident reporting
    first_aid_cases = models.PositiveIntegerField(default=0)
    medical_treatment_cases = models.PositiveIntegerField(default=0)
    non_lost_time_injuries = models.PositiveIntegerField(default=0)
    lost_time_injuries = models.PositiveIntegerField(default=0)
    fatalities = models.PositiveIntegerField(default=0)
=======
    
    ytd_work_related_accidents = models.PositiveIntegerField(default=0, editable=False)
    ytd_disabling_accidents = models.PositiveIntegerField(default=0, editable=False)
    ytd_fatal_accidents = models.PositiveIntegerField(default=0, editable=False)
    ytd_man_hours_lost = models.PositiveIntegerField(default=0, editable=False)
    ytd_motor_vehicle_accidents = models.PositiveIntegerField(default=0, editable=False)
    ytd_property_damaged = models.PositiveIntegerField(default=0, editable=False)
    ytd_she_meetings_conducted = models.PositiveIntegerField(default=0, editable=False)
    ytd_she_related_trainings = models.PositiveIntegerField(default=0, editable=False)
    ytd_wellness_programmes = models.PositiveIntegerField(default=0, editable=False)
    ytd_clear_up_campaigns = models.PositiveIntegerField(default=0, editable=False)
    ytd_she_inspections_conducted = models.PositiveIntegerField(default=0, editable=False)
    ytd_mock_drills_conducted = models.PositiveIntegerField(default=0, editable=False)
    
    
>>>>>>> 1b24c077b0267638fdc753da98de11aedc9afed6

    def save(self, *args, **kwargs):
        
        exposure_time = self.number_of_days * 7.5 * self.number_of_workers
        if exposure_time > 0:
            self.accident_frequency_rate = (self.work_related_accidents * 1_000_000 / exposure_time)
            self.injury_severity_rate = (self.man_hours_lost * 1_000_000 / exposure_time)
        else:
            self.accident_frequency_rate = 0
            self.injury_severity_rate = 0

        
        filters = {
            'year': self.year,
            'department': self.department,
            'regions': self.regions,
        }

        previous_reports = SafetyMonthlyReport.objects.filter(**filters).exclude(pk=self.pk).filter(month__lt=self.month)

        self.ytd_work_related_accidents = (
            sum(r.work_related_accidents for r in previous_reports) + self.work_related_accidents
        )
        self.ytd_disabling_accidents = (
            sum(r.disabling_accidents for r in previous_reports) + self.disabling_accidents
        )
        self.ytd_fatal_accidents = (
            sum(r.fatal_accidents for r in previous_reports) + self.fatal_accidents
        )
        self.ytd_man_hours_lost = (
            sum(r.man_hours_lost for r in previous_reports) + self.man_hours_lost
        )
        self.ytd_motor_vehicle_accidents = (
            sum(r.motor_vehicle_accidents for r in previous_reports) + self.motor_vehicle_accidents
        )
        self.ytd_property_damaged = (
            sum(r.property_damaged for r in previous_reports) + self.property_damaged
        )

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.year}-{self.month:02d} Safety Report"

class AccidentReport(models.Model):
    TYPE_Of_Accidents = [
        ('first aid case', 'first aid case'),
        ('medical treatment', 'medical treatment'),
        ('non lost time injury', 'non lost time injury'),
        ('lost time injury', 'lost time injury'),
        ('fatality', 'fatality'),
    ]
    Nature_of_Accidents = [
        ('electrical', 'electrical'),
        ('non_electrical', 'non_electrical'),
        ('road traffic', 'road traffic'),
    ]
    Nature_of_injury = [
        ('major', 'major'),
        ('minor','minor'),
    ]

    employee_involved = models.ForeignKey(UserProfile, on_delete=models.CASCADE, blank=True, null=True,related_name="accident_reports")
    department = models.ForeignKey(Sections, on_delete=models.DO_NOTHING, blank=True, null=True)
    regions = models.ForeignKey(Regions, on_delete=models.DO_NOTHING, blank=True, null=True)
    date = models.DateField()
    time = models.TimeField()
    cost_center = models.ForeignKey(CostCenter, on_delete=models.CASCADE, blank=True, null=True)
    ec_number = models.CharField(max_length=500)
    type_of_accident = models.CharField(max_length=500, choices=TYPE_Of_Accidents)
    nature_of_accident = models.CharField(max_length=600, choices=Nature_of_Accidents)
    nature_of_injury = models.CharField(max_length=400, choices=Nature_of_injury)
    circumstance_leading_to_accident = models.TextField(max_length=700)
    location_of_accident_giving_line_and_section_number = models.TextField(max_length=800)
    attach_pretask_risk_assessment = models.FileField(upload_to='risk_assessments/', blank=True, null=True)
    operation_of_protective_devices = models.TextField(max_length=600)
    attach_photographs = models.ImageField(upload_to='accident_photos/', blank=True, null=True)
    steps_taken_on_the_short_term = models.CharField(max_length=700)






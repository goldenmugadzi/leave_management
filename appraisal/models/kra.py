from django.db import models
from django.contrib.auth import get_user_model
from helpers.models.timestamp import TimeStamp
from .helpers import YearQuarter
from .appraisal import Appraisal

User = get_user_model()

class KeyResultArea(TimeStamp):
    created_by = models.ForeignKey(User, on_delete=models.RESTRICT, related_name="kra_creator", null=True)
    updated_by = models.ForeignKey(User, on_delete=models.RESTRICT, related_name="kra_creator_updater", null=True)
    key_result_area_description = models.CharField(max_length=500, unique=True)
    goal_description = models.CharField(max_length=500)
    
    def __str__(self):
        return f"{self.key_result_area_description}"
    
class KeyResultAreaOutCome(TimeStamp):
    key_result_area = models.ForeignKey(KeyResultArea, on_delete=models.RESTRICT, related_name="key_result_area_ref", null=True, blank=True)
    outcome_description = models.CharField(max_length=500)
    
    def __str__(self):
        return f"{self.key_result_area.key_result_area_description}"
    

class AppraisalKra(TimeStamp):
    appraisal = models.ForeignKey(Appraisal, on_delete=models.RESTRICT, related_name="appraisal_kra_user_appraisal", null=True, blank=True)
    quarter = models.ForeignKey(YearQuarter, on_delete=models.RESTRICT)
    key_result_area = models.ForeignKey(KeyResultArea, on_delete=models.RESTRICT, related_name="key_result_area", null=True, blank=True)

    def __str__(self):
        return f"{self.appraisal}"

    @property
    def get_name(self):
        return self.key_result_area.name

    # @property
    # def get_weight(self):
    #     return self.key_result_area.weight


PERFORMANCE_INDICATOR = [
        ('Quantity', 'Quantity'),
        ('Quality', 'Quality'),
        ('Timeliness', 'Timeliness'),
        ('Cost', 'Cost'),
    ]

class Activity(TimeStamp):
    appraisal_kra = models.ForeignKey(AppraisalKra, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank=False, null=False)
    description = models.TextField()
    weight = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name_plural = "Activities"
        
class PerformanceDimension(TimeStamp):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name="performance_indicator_activity")
    performance_indicator = models.CharField(max_length=30, choices=PERFORMANCE_INDICATOR, null=True, blank=True)
    description = models.TextField()
    weight = models.DecimalField(max_digits=5, decimal_places=2)
    agreed_target = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    allowable_variance = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    is_applicable = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.activity} - {self.performance_indicator}"
    
APPRAISAL_KRA_REVIEWER_STATUS_CHOICES = [
    ("PENDING", "PENDING"),
    ("ACCEPT", "ACCEPT"),
    ("REJECT", "REJECT"),
]

class TargetScore(TimeStamp):
    performance_dimension = models.OneToOneField(PerformanceDimension, on_delete=models.CASCADE, null=True, blank=True)
    score = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    comments = models.TextField(blank=True, null=True)
    is_scored = models.BooleanField(default=False)
    appraiser_confirmation = models.CharField(choices=APPRAISAL_KRA_REVIEWER_STATUS_CHOICES, default=APPRAISAL_KRA_REVIEWER_STATUS_CHOICES[0][0], max_length=10) 
    
    def __str__(self):
        return f"{self.performance_dimension}"
    
class ScoreDocument(TimeStamp):
    target_score = models.ForeignKey(TargetScore, on_delete=models.CASCADE, related_name='documents')
    name = models.CharField(max_length=255, blank=False, null=False)
    documents = models.FileField(upload_to='uploads/appraisal/score_attachments')

    def __str__(self):
        return f"Document for {self.target_score}"


class AppraisalWorkflow(TimeStamp):
    appraisal = models.ForeignKey(Appraisal, on_delete=models.RESTRICT, related_name="approval_appraisal", null=True, blank=True)
    stage_name = models.CharField(max_length=255)
    stage_num = models.PositiveIntegerField()
    is_completed = models.BooleanField(default=False)
    updated_by = models.ForeignKey(User, on_delete=models.RESTRICT, related_name="approve_user", null=True, blank=True)

    def __str__(self):
        return f"Approval {self.stage_name} - {self.stage_num} for {self.appraisal}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['appraisal', 'stage_num'],
                name='unique_stage_per_appraisal'
            )
        ]



class AppraisalKraReviewerStatus(TimeStamp):
    appraisal_kra = models.OneToOneField(AppraisalKra, on_delete=models.RESTRICT)
    status = models.CharField(max_length=10, choices=APPRAISAL_KRA_REVIEWER_STATUS_CHOICES, default=APPRAISAL_KRA_REVIEWER_STATUS_CHOICES[0][0])
    comment = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.appraisal_kra}"


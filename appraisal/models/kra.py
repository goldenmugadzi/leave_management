from django.db import models
from django.contrib.auth import get_user_model
from helpers.models.timestamp import TimeStamp
from .helpers import YearQuarter
from .appraisal import Appraisal

User = get_user_model()

class KeyResultArea(TimeStamp):
    appraisal = models.ForeignKey(Appraisal, on_delete=models.RESTRICT, related_name="user_kra_appraisal", null=True, blank=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    weight = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)

    def __str__(self):
        return f"{self.name}"


class AppraisalKra(TimeStamp):
    appraisal = models.ForeignKey(Appraisal, on_delete=models.RESTRICT, related_name="appraisal_kra_user_appraisal", null=True, blank=True)
    quarter = models.ForeignKey(YearQuarter, on_delete=models.RESTRICT)
    new_kra = models.ForeignKey(KeyResultArea, on_delete=models.RESTRICT, related_name="new_kra", null=True, blank=True)
    assigned_kra = models.ForeignKey("Activity", on_delete=models.RESTRICT, related_name="activity", null=True, blank=True)

    def __str__(self):
        return f"{self.appraisal}"

    def is_assigned_kra(self):
        assigned_kra = self.assigned_kra != None
        return assigned_kra

    def is_new_kra(self):
        new_kra = self.new_kra != None
        return new_kra

    @property
    def get_name(self):
        if self.is_assigned_kra():
            return self.assigned_kra.name
        if self.is_new_kra():
            return self.new_kra.name

    @property
    def get_weight(self):
        if self.is_assigned_kra():
            return self.assigned_kra.weight
        if self.is_new_kra():
            return self.new_kra.weight

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(new_kra__isnull=False, assigned_kra__isnull=True) |
                    models.Q(new_kra__isnull=True, assigned_kra__isnull=False)
                ),
                name="only_one_reference_allowed"
            )
        ]


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
    performance_indicator = models.CharField(max_length=30, choices=PERFORMANCE_INDICATOR, null=True, blank=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2)
    agreed_target = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    allowable_variance = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    assigned_user = models.ForeignKey(User, on_delete=models.RESTRICT, null=True)

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
    
    def __str__(self):
        return f"{self.performance_indicator}"

class TargetScore(TimeStamp):
    performance_dimension = models.OneToOneField(PerformanceDimension, on_delete=models.CASCADE, null=True, blank=True)
    score = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    comments = models.TextField(blank=True)
    is_scored = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.performance_dimension}"
    
class ScoreDocument(TimeStamp):
    target_score = models.ForeignKey(TargetScore, on_delete=models.CASCADE, related_name='documents')
    document = models.FileField(upload_to='uploads/appraisal/score_attachments')

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


APPRAISAL_KRA_REVIEWER_STATUS_CHOICES = [
    ("PENDING", "PENDING"),
    ("ACCEPT", "ACCEPT"),
    ("REJECT", "REJECT"),
]

class AppraisalKraReviewerStatus(TimeStamp):
    appraisal_kra = models.OneToOneField(AppraisalKra, on_delete=models.RESTRICT)
    status = models.CharField(max_length=10, choices=APPRAISAL_KRA_REVIEWER_STATUS_CHOICES, default=APPRAISAL_KRA_REVIEWER_STATUS_CHOICES[0][0])
    comment = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.appraisal_kra}"


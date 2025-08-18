from django.db import models
from django.contrib.auth import get_user_model
from helpers.models.timestamp import TimeStamp
from .helpers import YearQuarter
from .appraisal import Appraisal
from .departmental_workplan import DepartmentOutput, OutPutPerformanceDimension

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
    

class AppraisalDepartmentOutput(TimeStamp):
    appraisal = models.ForeignKey(Appraisal, on_delete=models.RESTRICT, related_name="appraisal_output", null=True, blank=True)
    department_output = models.ForeignKey(DepartmentOutput, on_delete=models.RESTRICT, related_name="appraisal_output", null=True, blank=True)
    year_quarter = models.ForeignKey(YearQuarter, on_delete=models.RESTRICT, related_name="quarterly_year")
    
    def __str__(self):
        return f"{self.appraisal} - {self.year_quarter} - {self.department_output}"
    
APPRAISAL_KRA_REVIEWER_STATUS_CHOICES = [
    ("PENDING", "PENDING"),
    ("ACCEPT", "ACCEPT"),
    ("REJECT", "REJECT"),
]

class AppraisalOutPutPerformanceDimensionScore(TimeStamp):
    appraisal_department_output = models.ForeignKey(AppraisalDepartmentOutput, on_delete=models.RESTRICT, related_name="appraisal_department_output_obj", null=True, blank=True)
    performance_dimension = models.ForeignKey(OutPutPerformanceDimension, on_delete=models.RESTRICT, related_name="performance_dimension", null=True, blank=True)
    score = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    comments = models.TextField(blank=True, null=True)
    is_scored = models.BooleanField(default=False)
    appraiser_confirmation = models.CharField(choices=APPRAISAL_KRA_REVIEWER_STATUS_CHOICES, default=APPRAISAL_KRA_REVIEWER_STATUS_CHOICES[0][0], max_length=10) 

    def __str__(self):
        return f"{self.appraisal_department_output} - {self.performance_dimension}"

class ScoreDocument(TimeStamp):
    performance_dimension_score = models.ForeignKey(AppraisalOutPutPerformanceDimensionScore, on_delete=models.RESTRICT, related_name='performance_dimension_score_obj', null=True, blank=True)
    name = models.CharField(max_length=255, blank=False, null=False)
    documents = models.FileField(upload_to='uploads/appraisal/score_attachments')

    def __str__(self):
        return f"Document for {self.performance_dimension_score}"


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


class AppraisalDepartmentOutputReviewerStatus(TimeStamp):
    performance_dimension_score = models.OneToOneField(AppraisalOutPutPerformanceDimensionScore, on_delete=models.RESTRICT, related_name="appraisal_department_output_reviewer_status", null=True)
    status = models.CharField(max_length=10, choices=APPRAISAL_KRA_REVIEWER_STATUS_CHOICES, default=APPRAISAL_KRA_REVIEWER_STATUS_CHOICES[0][0])
    comment = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.performance_dimension_score}"


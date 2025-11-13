from django.contrib import admin
from .models import (Appraisal, Experience, AppraisalExperience,
    PerformanceProgressWeakness, PerformanceProgressReview,
    PerformanceProgressStrength, Competency, JobCompetency, InterventionStrategy, TrainingAndDevelopment,
    KeyResultArea, YearQuarter, AppraisalWorkflow, ScoreDocument,
    KeyResultAreaOutCome, DepartmentObjective, DepartmentOutput, OutPutPerformanceDimension,
    AppraisalDepartmentOutput, AppraisalOutPutPerformanceDimensionScore, PersonalAttribute, 
    AppraiseePersonalAttribute, AppraisalDepartmentOutputReviewerStatus, AppraisalApprovalWorkFlowQuarter,
    AppraisalOverallComments, AppraisalConfirmationStatus
)

# Register your models here.

admin.site.register(Appraisal)
admin.site.register(Experience)
admin.site.register(AppraisalExperience)
admin.site.register(AppraisalDepartmentOutputReviewerStatus)

admin.site.register(PerformanceProgressStrength)
admin.site.register(PerformanceProgressWeakness)
admin.site.register(PerformanceProgressReview)

admin.site.register(Competency)
admin.site.register(JobCompetency)
admin.site.register(InterventionStrategy)
admin.site.register(TrainingAndDevelopment)

admin.site.register(KeyResultArea)
admin.site.register(YearQuarter)

admin.site.register(AppraisalWorkflow)
admin.site.register(ScoreDocument)
admin.site.register(KeyResultAreaOutCome)
admin.site.register(DepartmentObjective)
admin.site.register(DepartmentOutput)
admin.site.register(OutPutPerformanceDimension)

admin.site.register(AppraisalDepartmentOutput)
admin.site.register(AppraisalOutPutPerformanceDimensionScore)

admin.site.register(PersonalAttribute)
admin.site.register(AppraiseePersonalAttribute)
admin.site.register(AppraisalApprovalWorkFlowQuarter)
admin.site.register(AppraisalOverallComments)
admin.site.register(AppraisalConfirmationStatus)


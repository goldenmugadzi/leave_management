from django.contrib import admin
from .models import (Appraisal, Experience, AppraisalExperience,
    PerformanceProgressWeakness, PerformanceProgressReview,
    PerformanceProgressStrength, Competency, JobCompetency, InterventionStrategy, TrainingAndDevelopment,
    KeyResultArea, Activity, YearQuarter, AppraisalKra, TargetScore, AppraisalWorkflow
)

# Register your models here.

admin.site.register(Appraisal)
admin.site.register(Experience)
admin.site.register(AppraisalExperience)

admin.site.register(PerformanceProgressStrength)
admin.site.register(PerformanceProgressWeakness)
admin.site.register(PerformanceProgressReview)

admin.site.register(Competency)
admin.site.register(JobCompetency)
admin.site.register(InterventionStrategy)
admin.site.register(TrainingAndDevelopment)

admin.site.register(KeyResultArea)
admin.site.register(Activity)
admin.site.register(YearQuarter)
admin.site.register(AppraisalKra)
admin.site.register(TargetScore)
admin.site.register(AppraisalWorkflow)

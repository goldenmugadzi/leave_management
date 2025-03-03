from enum import Enum

class ApprovalStageData(Enum):
    accept_appraisal = "Accept Appraisal"
    scoring = "Scoring"
    set_performance_progress_review = "Set Performance Progress Review"
    set_training_and_development_needs = "Training And Development"
    reviewed = "Reviewed"

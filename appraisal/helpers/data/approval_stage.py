from enum import Enum

class ApprovalStageData(Enum):
    accept_appraisal = "Accept Appraisal"
    scoring = "Scoring"
    appraiser_review = "Appraiser Review"
    section_head_review = "Section Head Review"
    set_training_and_development_needs = "Training And Development"
    set_performance_progress_review = "Performance Progress Review"
    hr_review = "HR Review"

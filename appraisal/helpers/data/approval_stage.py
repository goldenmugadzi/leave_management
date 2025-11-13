from enum import Enum

class ApprovalStageData(Enum):
    accept_appraisal = "Accept Appraisal"
    scoring = "Scoring"
    appraiser_review = "Appraiser Confirmation"
    set_training_and_development_needs = "Training And Development"
    set_performance_progress_review = "Performance Progress Review"
    set_personal_attributes = "Personal Attributes"
    overall_comments = "Overall Comments"
    hr_review = "HR Confirmation"
    section_head_review = "Reviewer Confirmation"

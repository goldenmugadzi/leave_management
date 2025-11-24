from enum import Enum

class ApprovalStageData(Enum):
    scoring = {"stage_name": "Scoring", "description": "Appraisee To Score in Section 2 - Performance Plan and Assessment"}
    appraiser_review = {"stage_name": "Appraiser Confirmation", "description": "Appraiser To Confirm Appraisee`s Scoring in Section 2 - Performance Plan and Assessment"}
    set_training_and_development_needs = {"stage_name": "Training And Development", "description": "Appraiser to set Training and Development Needs in Section 3 - Training and Development Needs"}
    set_performance_progress_review = {"stage_name": "Performance Progress Review", "description": "Appraiser to set Performance Progress Review in Section 4 - Performance Progress Reviews"}
    set_personal_attributes = {"stage_name": "Personal Attributes", "description": "Appraiser to set Personal Attributes in Section 5 - Final Performance Assessment and Rating"}
    overall_comments = {"stage_name": "Overall Comments", "description": "Appraiser to set Overall Comments in Section 5 - Final Performance Assessment and Rating"}
    hr_review = {"stage_name": "HR Confirmation", "description": "HR to confirm the appraisal process within the Appraisal Details"}
    section_head_review = {"stage_name": "Reviewer Confirmation", "description": "Reviewer to confirm the appraisal process within the Appraisal Details"}

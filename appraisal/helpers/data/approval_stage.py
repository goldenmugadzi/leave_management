from enum import Enum

USER_RESPONSIBLE = [
    ("appraisee", "appraisee"),
    ("appraiser", "appraiser"),
    ("reviewer", "reviewer"),
    ("hr", "hr")
]

APPRAISEE = USER_RESPONSIBLE[0][1]
APPRAISER = USER_RESPONSIBLE[1][1]
REVIEWER = USER_RESPONSIBLE[2][1]
HR = USER_RESPONSIBLE[3][1]

class SectionStages(Enum):
    section_1 = "Personal Details"
    section_2 = "Performance Plan and Assessment"
    section_3 = "Training and Development Needs"
    section_4 = "Performance Progress Review"
    section_5 = "Final Performance Assessment and Rating"
    section_6 = "Appraisal Detail"
    
    def url(self):
        return {
            SectionStages.section_1: "update_appraisal",
            SectionStages.section_2: "appraisal_dept_output_index",
            SectionStages.section_3: "training_development_index",
            SectionStages.section_4: "performance_review_detail",
            SectionStages.section_5: "appraisal_final_result_index",
            SectionStages.section_6: "appraisal_detail",
        }.get(self, "")

class ApprovalStageData(Enum):
    scoring = {"stage_name": "Scoring", "description": "Appraisee To Score in Section 2 - Performance Plan and Assessment", "set_by": APPRAISEE, "section_step": SectionStages.section_2.value}
    appraiser_review = {"stage_name": "Appraiser Confirmation", "description": "Appraiser To Confirm Appraisee`s Scoring in Section 2 - Performance Plan and Assessment", "set_by": APPRAISER, "section_step": SectionStages.section_2.value}
    set_training_and_development_needs = {"stage_name": "Training And Development", "description": "Appraiser to set Training and Development Needs in Section 3 - Training and Development Needs", "set_by": APPRAISER, "section_step": SectionStages.section_3.value}
    set_performance_progress_review = {"stage_name": "Performance Progress Review", "description": "Appraiser to set Performance Progress Review in Section 4 - Performance Progress Reviews", "set_by": APPRAISER, "section_step": SectionStages.section_4.value}
    set_personal_attributes = {"stage_name": "Personal Attributes", "description": "Appraiser to set Personal Attributes in Section 5 - Final Performance Assessment and Rating", "set_by": APPRAISER, "section_step": SectionStages.section_5.value}
    overall_comments = {"stage_name": "Overall Comments", "description": "Appraiser to set Overall Comments in Section 5 - Final Performance Assessment and Rating", "set_by": APPRAISER, "section_step": SectionStages.section_5.value}
    hr_review = {"stage_name": "HR Confirmation", "description": "HR to confirm the appraisal process within the Appraisal Details", "set_by": HR, "section_step": SectionStages.section_6}
    section_head_review = {"stage_name": "Reviewer Confirmation", "description": "Reviewer to confirm the appraisal process within the Appraisal Details", "set_by": REVIEWER, "section_step": SectionStages.section_6.value}

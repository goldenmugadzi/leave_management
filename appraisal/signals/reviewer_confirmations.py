from django.db.models.signals import post_save
from django.dispatch import receiver
from loguru import logger
from ..models import AppraisalConfirmationStatus
from ..models.kra import APPRAISAL_KRA_REVIEWER_STATUS_CHOICES, REVIEWERS_CONFIRMATION_STATUS
from ..helpers.data.approval_stage import ApprovalStageData
from ..helpers.setters import handle_stage_completion
from loguru import logger

@receiver(post_save, sender=AppraisalConfirmationStatus, dispatch_uid="appraisal_reviewers_confirmation")
def appraisal_reviewers_confirmation_stages_handler(sender, instance, created, **kwargs):
    if not created:
        try:
            logger.info(f"[AppraisalConfirmationStatusSignal] appraisal_reviewers_confirmation_stages_handler for AppraisalConfirmationStatus pk: {instance.id}, started")
            if instance.confirmation_status == APPRAISAL_KRA_REVIEWER_STATUS_CHOICES[1][0]:
                stage_name = None
                if instance.confirmed_by == REVIEWERS_CONFIRMATION_STATUS[1][0]:
                    # ============= Reviewer Stage============
                    stage_name = ApprovalStageData.section_head_review.value["stage_name"]
                elif instance.confirmed_by == REVIEWERS_CONFIRMATION_STATUS[2][0]:
                    # ============= Hr Stage============
                    stage_name = ApprovalStageData.hr_review.value["stage_name"]

                if stage_name is not None:
                    handle_stage_completion(
                        appraisal_id=instance.appraisal.id,
                        year_quarter_id=instance.year_quarter.id,
                        stage_name=stage_name
                    )
        except Exception as e:
            logger.error(f"[AppraisalConfirmationStatusSignal] appraisal_reviewers_confirmation_stages_handler for AppraisalConfirmationStatus pk: {instance.id}, failed with error: {e}")

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Q
from ..repository.kra import ApprasialKraReviewerStatusRepository
from ..repository.approval import AppraisalWorkflowRepository
from ..models.kra import APPRAISAL_KRA_REVIEWER_STATUS_CHOICES, AppraisalKraReviewerStatus
from ..models.helpers import QuarterChoices
from loguru import logger


@receiver(post_save, sender=AppraisalKraReviewerStatus, dispatch_uid="appraisal-reviewer-status-uid")
def appraisal_reviewer_workflow_handler(sender, instance, created, **kwargs):
    if not created and instance.status == APPRAISAL_KRA_REVIEWER_STATUS_CHOICES[1][0]:
        logger.info(f"[Approval Workflow stage] Reviewer stage with AppraisalKraReviewerStatus pk {instance.id} signal handler init .....")
        try:
            appraisal_kra_quarter_obj = instance.appraisal_kra.quarter
            reviewer_status_repo = ApprasialKraReviewerStatusRepository()
            reviewer_status_year_qr = reviewer_status_repo.fetch_by_quarter_year(year=appraisal_kra_quarter_obj.year)

            if not reviewer_status_year_qr.exists():
                logger.info(f"[Approval Workflow stage] Reviewer stage with AppraisalKraReviewerStatus pk {instance.id}, has no objects for year: {appraisal_kra_quarter_obj.year}")
                return None

            reviewer_status_quarter_qr = reviewer_status_year_qr.filter(
                Q(appraisal_kra__quarter__quarter=QuarterChoices.Q1),
                Q(appraisal_kra__quarter__quarter=QuarterChoices.Q2),
                Q(appraisal_kra__quarter__quarter=QuarterChoices.Q3),
                Q(appraisal_kra__quarter__quarter=QuarterChoices.Q4),
            )
            
            if not reviewer_status_quarter_qr.exists():
                logger.info(f"[Approval Workflow stage] Reviewer stage with AppraisalKraReviewerStatus pk {instance.id}, has no objects for all quarters")
                return None
            
            reviewer_status_not_accepted_qr = reviewer_status_quarter_qr.filter(Q(status=APPRAISAL_KRA_REVIEWER_STATUS_CHOICES[0][0]) | Q(status=APPRAISAL_KRA_REVIEWER_STATUS_CHOICES[1][0]))
            if reviewer_status_not_accepted_qr.exists():
                logger.info(f"[Approval Workflow stage] Reviewer stage with AppraisalKraReviewerStatus pk {instance.id}, has some objects not accepted yet for year: {appraisal_kra_quarter_obj.year} all quarters")
                return None
            
            # Update Reviewer stage as completed
            appraisal_workflow_repo = AppraisalWorkflowRepository()
            reviewer_workflow_stage_obj = appraisal_workflow_repo.retrieve_by_appraisal(appraisal_id=instance.appraisal_kra.appraisal.id)
            
            appraisal_workflow_repo.update(workflow_object=reviewer_workflow_stage_obj, is_completed=True, updated_by=appraisal_kra_quarter_obj.appraisal.reviewer)
            logger.success(f"[Approval Workflow stage] Reviewer stage with AppraisalKraReviewerStatus pk {instance.id} completed successfully")
        except Exception as e:
            logger.error(f"[Approval Workflow stage] Reviewer stage with AppraisalKraReviewerStatus pk {instance.id} signal handler, failed with error: {e} ")
            return None
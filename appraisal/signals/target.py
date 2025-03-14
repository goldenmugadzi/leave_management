from django.db.models.signals import post_save
from django.dispatch import receiver
from ..models import TargetScore
from ..repository.kra import TargetScoreRepository
from ..repository.approval import AppraisalWorkflowRepository
from ..helpers.data.approval_stage import ApprovalStageData

from loguru import logger

    
@receiver(post_save, sender=TargetScore, dispatch_uid="appraisal_approval_workflow_scoring_stage")
def set_appraisal_scoring_stage_completed(sender, instance, created, **kwargs):
    if not created:
        try:
            activity_object = instance.activity
            logger.info(f"[Approval Workflow stage] Scoring stage for Appraisal Activity: {activity_object} pk: {activity_object.id} handler initialized ...")
            score_repo = TargetScoreRepository()
            score_qr = score_repo.fetch_by_appraisal_id(appraisal_id=activity_object.appraisal_kra.appraisal.id)
            
            if not score_qr.exists():
                logger.error(f"[Approval Workflow stage] Scoring stage for Appraisal Activity: {activity_object} pk: {activity_object.id}, Scoring objects not found")
                return None
            
            unscored_activity_score_qr = score_qr.filter(is_scored=False)
            if unscored_activity_score_qr.exists():
                logger.info(f"[Approval Workflow stage] Scoring stage for Appraisal Activity: {activity_object} pk: {activity_object.id}, Scoring objects not scored exists")
                return None
            
            appraisal_object = score_qr.first().activity.appraisal_kra.appraisal
            workflow_repo = AppraisalWorkflowRepository()
            workflow_qr = workflow_repo.retrieve_by_appraisal(appraisal_id=appraisal_object.id)
            
            if not workflow_qr.exists():
                logger.error(f"[Approval Workflow stage] Scoring stage for Appraisal Activity: {activity_object} pk: {activity_object.id}, All stages not found")
                return None            
            
            workflow_scoring_qr = workflow_qr.filter(stage_name=ApprovalStageData.scoring.value)
            if not workflow_scoring_qr.exists():
                logger.error(f"[Approval Workflow stage] Scoring stage for Appraisal Activity: {activity_object} pk: {activity_object.id}, {ApprovalStageData.scoring.value} stage  not found")
                return None
              
            workflow_repo.update(workflow_object=workflow_scoring_qr.first(), is_completed=True, updated_by=appraisal_object.appraiser)
            
            logger.success(f"[Approval Workflow stage] Scoring stage for Appraisal Activity {activity_object} pk: {activity_object.id} completed")
        except Exception as e:
            return None


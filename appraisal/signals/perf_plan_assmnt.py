from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver
from loguru import logger
from ..models import AppraisalOutPutPerformanceDimensionScore, AppraisalDepartmentOutputReviewerStatus
from ..models.kra import APPRAISAL_KRA_REVIEWER_STATUS_CHOICES
from ..repository.kra import AppraisalOutPutPerformanceDimensionScoreRepository, ApprasialKraReviewerStatusRepository
from ..repository.approval import AppraisalWorkflowRepository
from ..helpers.getters.approval import ApprovalStageGetterHandler
from ..helpers.data.approval_stage import ApprovalStageData

@receiver(post_save, sender=AppraisalOutPutPerformanceDimensionScore, dispatch_uid="appraisal_dimension_score")
def appraisal_dimension_score_completed_scoring_stage_handler(sender, instance, created, **kwargs):
    if not created:
        try:
            logger.info(f"[ScoringStageSignalHandler] appraisal_dimension_score_completed_scoring_stage_handler with AppraisalOutPutPerformanceDimensionScore pk: {instance.id}, started")
            appraisal_department_output_obj = instance.appraisal_department_output
            
            repo = AppraisalOutPutPerformanceDimensionScoreRepository()
            qr = repo.fetch_by_appraisal_department_output_id(appraisal_department_output_id=appraisal_department_output_obj.id)
            unscored_qr = qr.filter(is_scored=False)
            
            if not unscored_qr.exists():
                logger.info(f"[ScoringStageSignalHandler] appraisal_dimension_score_completed_scoring_stage_handler with AppraisalOutPutPerformanceDimensionScore pk: {instance.id}, has unscored objects")
                
                appraisal_id = appraisal_department_output_obj.appraisal.id
                year_quarter_id = appraisal_department_output_obj.year_quarter.id
                
                workflow_repo = AppraisalWorkflowRepository()
                quarter_workflow_qr = workflow_repo.fetch_by_appraisal_id_quarter_id(
                    appraisal_id=appraisal_id,
                    year_quarter_id=year_quarter_id
                )
                
                approval_stage_handler = ApprovalStageGetterHandler()
                stage_num = approval_stage_handler.get_stage_num_by_name(
                    stage_name=ApprovalStageData.scoring.value["stage_name"]
                    )
                
                if stage_num != 0:
                    quarter_workflow_obj = quarter_workflow_qr.filter(stage_num=stage_num).first()
                    workflow_repo.update(
                        workflow_object=quarter_workflow_obj,
                        is_completed=True
                    )
                    logger.success(f"[ScoringStageSignalHandler] appraisal_dimension_score_completed_scoring_stage_handler with AppraisalWorkflowRepository pk: {quarter_workflow_obj.id}, is completed")
            else:
                logger.info(f"[ScoringStageSignalHandler] appraisal_dimension_score_completed_scoring_stage_handler with AppraisalOutPutPerformanceDimensionScore pk: {instance.id}, all objects scored")

        except Exception as e:
            logger.error(f"[ScoringStageSignalHandler] appraisal_dimension_score_completed_scoring_stage_handler AppraisalOutPutPerformanceDimensionScore pk: {instance.id}, failed with error: {e}")

@receiver(post_save, sender=AppraisalDepartmentOutputReviewerStatus, dispatch_uid="appraiser_confirmation_stage")
def appraisal_confirmation_completed_scoring_stage_handler(sender, instance, created, **kwargs):
    if not created:
        try:
            logger.info(f"[AppraiserConfirmationStageSignalHandler] appraisal_confirmation_completed_scoring_stage_handler with AppraisalDepartmentOutputReviewerStatus pk: {instance.id}, started")
            
            if instance.confirmation_status == APPRAISAL_KRA_REVIEWER_STATUS_CHOICES[1][0]:
                logger.info(f"[AppraiserConfirmationStageSignalHandler] appraisal_confirmation_completed_scoring_stage_handler with AppraisalDepartmentOutputReviewerStatus pk: {instance.id}, has unaccepted object")
                
                appraisal_id = instance.appraisal_department_output.appraisal.id
                year_quarter_id = instance.appraisal_department_output.year_quarter.id
                
                workflow_repo = AppraisalWorkflowRepository()
                quarter_workflow_qr = workflow_repo.fetch_by_appraisal_id_quarter_id(
                    appraisal_id=appraisal_id,
                    year_quarter_id=year_quarter_id
                )
                
                approval_stage_handler = ApprovalStageGetterHandler()
                stage_num = approval_stage_handler.get_stage_num_by_name(
                    stage_name=ApprovalStageData.appraiser_review.value["stage_name"]
                    )
                
                if stage_num != 0:
                    quarter_workflow_obj = quarter_workflow_qr.filter(stage_num=stage_num).first()
                    workflow_repo.update(
                        workflow_object=quarter_workflow_obj,
                        is_completed=True
                    )
                    logger.success(f"[AppraiserConfirmationStageSignalHandler] appraisal_confirmation_completed_scoring_stage_handler with AppraisalWorkflowRepository pk: {quarter_workflow_obj.id}, is completed")
        except Exception as e:
            logger.error(f"[AppraiserConfirmationStageSignalHandler] appraisal_confirmation_completed_scoring_stage_handler with AppraisalWorkflowRepository pk: {quarter_workflow_obj.id}, error: {e}")

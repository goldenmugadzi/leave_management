from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver
from loguru import logger
from ..models import PerformanceProgressReview, TrainingAndDevelopment
from ..repository.approval import AppraisalWorkflowRepository
from ..repository.performance import PerformanceReviewRepository
from ..repository.training import TrainingAndDevelopmentRepository
from ..helpers.data.approval_stage import ApprovalStageData

@receiver(m2m_changed, sender=PerformanceProgressReview.strengths.through, dispatch_uid="performance_progress_review_strengths_changed")
@receiver(m2m_changed, sender=PerformanceProgressReview.areas_of_weaknesses.through, dispatch_uid="performance_progress_review_weaknesses_changed")
def set_performance_progress_review_stage_completed(sender, instance, action, **kwargs):
    if action == "post_add":
        try:
            logger.info(f"[Approval Workflow stage] Performance Progress Review stage for Appraisal: {instance.appraisal} pk: {instance.appraisal.id} handler initialized ...")
            
            performance_review_repo = PerformanceReviewRepository()
            performance_review_qr = performance_review_repo.get_performance_by_appraisal_id(appraisal_id=instance.appraisal.id)
            if not performance_review_qr.exists():
                logger.error(f"[Approval Workflow stage] Performance Progress Review stage for Appraisal: {instance.appraisal} pk: {instance.appraisal.id}, Performance Review objects not found")
                return None
        
            appraisal_object = performance_review_qr.first().appraisal
            uncompleted_performance_review_qr = performance_review_qr.filter(is_completed=False)
            if uncompleted_performance_review_qr.exists():
                logger.info(f"[Approval Workflow stage] Performance Progress Review stage for Appraisal: {appraisal_object} pk: {appraisal_object.id}, Stages not completed")
                return None
            
            workflow_repo = AppraisalWorkflowRepository()
            workflow_qr = workflow_repo.retrieve_by_appraisal(appraisal_id=appraisal_object.id)
            
            if not workflow_qr.exists():
                logger.error(f"[Approval Workflow stage] Performance Progress Review stage for Appraisal: {appraisal_object} pk: {appraisal_object.id}, All stages not found")
                return None            
            
            workflow_scoring_qr = workflow_qr.filter(stage_name=ApprovalStageData.set_performance_progress_review.value)
            if not workflow_scoring_qr.exists():
                logger.error(f"[Approval Workflow stage] Performance Progress Review stage for Appraisal: {appraisal_object} pk: {appraisal_object.id}, {ApprovalStageData.set_performance_progress_review.value} stage  not found")
                return None
              
            workflow_repo.update(workflow_object=workflow_scoring_qr.first(), is_completed=True, updated_by=appraisal_object.appraiser)
            
            logger.success(f"[Approval Workflow stage] Performance Progress Review stage for Appraisal: {appraisal_object} pk: {appraisal_object.id}, {ApprovalStageData.set_performance_progress_review.value} completed")
        except Exception as e:
            logger.error(f"[Approval Workflow stage] Performance Progress Review stage for Appraisal: {instance.appraisal} pk: {instance.appraisal.id} handler, failed with error: {e}")
            return None
        

@receiver(post_save, sender=TrainingAndDevelopment, dispatch_uid="training_development_changed")
def set_training_development_stage_completed(sender, instance, created, **kwargs):
    if not created:
        try:
            appraisal_object = instance.appraisal
            logger.info(f"[Approval Workflow stage] Training development needs stage for Appraisal: {appraisal_object} pk: {appraisal_object.id} handler initialized ...")
            
            training_dev_repo = TrainingAndDevelopmentRepository()
            training_dev_qr = training_dev_repo.get_by_appraisal_id(appraisal_id=appraisal_object.id)
            if not training_dev_qr.exists():
                logger.error(f"[Approval Workflow stage] Training development needs stage for Appraisal: {appraisal_object} pk: {appraisal_object.id}, All objects not found")
                return None
        
            appraisal_object = training_dev_qr.first().appraisal
            uncompleted_training_dev_qr = training_dev_qr.filter(is_completed=False)
            if uncompleted_training_dev_qr.exists():
                logger.info(f"[Approval Workflow stage] Training development needs stage for Appraisal: {appraisal_object} pk: {appraisal_object.id}, Stages not completed")
                return None
            
            workflow_repo = AppraisalWorkflowRepository()
            workflow_qr = workflow_repo.retrieve_by_appraisal(appraisal_id=appraisal_object.id)
            
            if not workflow_qr.exists():
                logger.error(f"[Approval Workflow stage] Training development needs stage for Appraisal: {appraisal_object} pk: {appraisal_object.id}, All stages not found")
                return None            
            
            workflow_scoring_qr = workflow_qr.filter(stage_name=ApprovalStageData.set_training_and_development_needs.value)
            if not workflow_scoring_qr.exists():
                logger.error(f"[Approval Workflow stage] Training development needs stage for Appraisal: {appraisal_object} pk: {appraisal_object.id}, {ApprovalStageData.set_training_and_development_needs.value} stage  not found")
                return None
              
            workflow_repo.update(workflow_object=workflow_scoring_qr.first(), is_completed=True, updated_by=appraisal_object.appraiser)
            
            logger.success(f"[Approval Workflow stage] Training development needs stage for Appraisal: {appraisal_object} pk: {appraisal_object.id}, {ApprovalStageData.set_training_and_development_needs.value} completed")
        except Exception as e:
            logger.error(f"[Approval Workflow stage] Training development needs stage for Appraisal: {instance} pk: {instance.id}, failed with error: {e}")
            return None

from django import template
from ..helpers.getters.approval import ApprovalStagesHandler
from ..helpers.data.approval_stage import ApprovalStageData
from ..helpers.getters.approval import ApprovalWorkflowQuarterStagesStrategyContext, ScoringStageStrategy, PerformanceReviewStageStrategy, TrainingAndDevelopmentStageStrategy, ReviewStageStrategy, AppraiserReviewStageStrategy, ReviewerReviewStageStrategy, HrReviewStageStrategy, AppraisalPersonalAttributesStrategy, AppraisalOverallCommentStrategy
from loguru import logger

register = template.Library()

@register.filter
def get_current_approval_stage(appraisal_int: int):
    data = {"current_stage": None}
    if not isinstance(appraisal_int, int):
        logger.error(f"[get_current_approval_stage()] templatetags, Invalid type for appraisal_int: Expected int, got {type(appraisal_int).__name__}")
        return data
    
    try:
        handler = ApprovalStagesHandler(appraisal_id=appraisal_int)
        completed_stages = handler.get_completed_approval_queryset()
        current_stage = None
        if completed_stages is not None:
            current_stage = completed_stages.last()
        else:
            uncompleted_stages = handler.get_uncompleted_approval_queryset()
            current_stage = uncompleted_stages.first()
        
        data["current_stage"] = current_stage
        return data
        
    except Exception as e:
        logger.error(f"[get_current_approval_stage()] templatetags, failed with error: {e}")
        return None
    
@register.filter
def get_approval_stage(appraisal_int: int):
    if not isinstance(appraisal_int, int):
        logger.error(f"[get_approval_stage()] templatetags, Invalid type for appraisal_int: Expected int, got {type(appraisal_int).__name__}")
    
    try:
        handler = ApprovalStagesHandler(appraisal_id=appraisal_int)
        return handler.get_current_and_next_stage()
        
    except Exception as e:
        logger.error(f"[get_approval_stage()] templatetags, failed with error: {e}")
        return None

@register.simple_tag
def get_stage_data(stage_name: str, appraisal_kra_id: int):
    data = []
    if not isinstance(stage_name, str) or not isinstance(appraisal_kra_id, int):
        logger.error(f"[get_stage_data()] templatetags, Invalid type for stage_name: {stage_name}, Expected str, got {type(stage_name).__name__} || or appraisal_kra_id: {appraisal_kra_id}, Expects int, got: {type(appraisal_kra_id).__name__}")
        return data
    
    match stage_name:
        
        case ApprovalStageData.scoring.value:
            data = ApprovalWorkflowQuarterStagesStrategyContext(strategy=ScoringStageStrategy()).get_stage_quarters_approval(appraisal_kra_id=appraisal_kra_id)
        case ApprovalStageData.appraiser_review.value:
            data = ApprovalWorkflowQuarterStagesStrategyContext(strategy=AppraiserReviewStageStrategy()).get_stage_quarters_approval(appraisal_kra_id=appraisal_kra_id)
        case ApprovalStageData.set_training_and_development_needs.value:
            data = ApprovalWorkflowQuarterStagesStrategyContext(strategy=TrainingAndDevelopmentStageStrategy()).get_stage_quarters_approval(appraisal_kra_id=appraisal_kra_id)
        case ApprovalStageData.set_performance_progress_review.value:
            data = ApprovalWorkflowQuarterStagesStrategyContext(strategy=PerformanceReviewStageStrategy()).get_stage_quarters_approval(appraisal_kra_id=appraisal_kra_id)
        case ApprovalStageData.set_personal_attributes.value:
            data = ApprovalWorkflowQuarterStagesStrategyContext(strategy=AppraisalPersonalAttributesStrategy()).get_stage_quarters_approval(appraisal_kra_id=appraisal_kra_id)
        case ApprovalStageData.overall_comments.value:
            data = ApprovalWorkflowQuarterStagesStrategyContext(strategy=AppraisalOverallCommentStrategy()).get_stage_quarters_approval(appraisal_kra_id=appraisal_kra_id)
        case ApprovalStageData.hr_review.value:
            data = ApprovalWorkflowQuarterStagesStrategyContext(strategy=HrReviewStageStrategy()).get_stage_quarters_approval(appraisal_kra_id=appraisal_kra_id)
        case ApprovalStageData.section_head_review.value:
            data = ApprovalWorkflowQuarterStagesStrategyContext(strategy=ReviewerReviewStageStrategy()).get_stage_quarters_approval(appraisal_kra_id=appraisal_kra_id)
    return data
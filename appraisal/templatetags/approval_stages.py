from django import template
from ..helpers.getters.approval import ApprovalStagesHandler
from ..helpers.data.approval_stage import ApprovalStageData, SectionStages
from ..helpers.getters.approval import ApprovalWorkflowQuarterStagesStrategyContext, ScoringStageStrategy, PerformanceReviewStageStrategy, TrainingAndDevelopmentStageStrategy, AppraiserReviewStageStrategy, ReviewerReviewStageStrategy, HrReviewStageStrategy, AppraisalPersonalAttributesStrategy, AppraisalOverallCommentStrategy, ApprovalStageGetterHandler
from ..view.helper import ApprovalStagesTemplateHandler
from ..repository.appraisal import AppraisalRepository
from ..helpers.getters.sections import SectionsStagesHandler
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

@register.filter
def get_user_responsible(approval_stage_id: int):
    try:
        handler = ApprovalStageGetterHandler()
        return handler.get_user_responsible(approval_stage_id=approval_stage_id)
        
    except Exception as e:
        logger.error(f"[get_user_responsible()] templatetags, failed with error: {e}")
        return None
    
@register.filter
def get_approval_stage_data(appraisal_id):
    try:
        repo = AppraisalRepository()
        appraisal_object = repo.get_appraisal_by_pk(appraisal_id=appraisal_id)
        if appraisal_object is None:
            raise Exception("appraisal object not found")
        
        handler = ApprovalStagesTemplateHandler(appraisal_object=appraisal_object)
        return handler.get_context_data
        
    except Exception as e:
        logger.error(f"[get_approval_stage_date()] templatetags, failed with error: {e}")
        return None
    
@register.filter
def get_approval_stage_url(stage_name: str):
    try:
        for approval_stage in ApprovalStageData:
            stage_dict = approval_stage.value
            
            if stage_dict["stage_name"].lower() == stage_name.lower():
                section_stages_handler = SectionsStagesHandler()
                section_step = stage_dict["section_step"]
                
                if isinstance(section_step, SectionStages):
                    section_step = section_step.value
                
                return section_stages_handler.get_section_url_section_value(
                    section_value=section_step
                )
                
        return None
        
    except Exception as e:
        logger.error(f"[get_approval_stage_url()] templatetags stage_name: {stage_name}, failed with error: {e}")
        return None
    

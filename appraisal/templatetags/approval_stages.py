from django import template
from ..helpers.getters.approval import ApprovalStagesHandler
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
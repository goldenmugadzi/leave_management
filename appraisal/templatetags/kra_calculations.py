from django import template
from ..services.kra import TargetScoreService
from ..repository.kra import TargetScoreRepository
from loguru import logger
from loguru import logger
register = template.Library()

@register.filter
def get_target_rating(target_id)->int:
    if not isinstance(target_id, int):
        logger.error(f"Invalid type for target_id: Expected int, got {type(activity_id).__name__}")
        return 0
    
    repo = TargetScoreRepository()
    service_handler = TargetScoreService(target_score_repository=repo)
    
    try:
        return service_handler.calculate_activity_score_use_case(target_id=target_id)
    except Exception as e:
        logger.error(e)
        return 0
    
@register.filter
def get_activity_average_weighted_score(activity_id)->float:
    if not isinstance(activity_id, int):
        logger.error(f"Invalid type for activity_id: Expected int, got {type(activity_id).__name__}")
        return 0.0

    repo = TargetScoreRepository()
    service_handler = TargetScoreService(target_score_repository=repo)
    
    try:
        return service_handler.calculate_average_weighted_score_per_activity(activity_id=activity_id)
    except Exception as e:
        logger.error(e)
        return 0.0
    

from django import template
from ..services.kra import TargetScoreService
from ..repository.kra import TargetScoreRepository
from loguru import logger
register = template.Library()

@register.filter
def get_target_rating(target_id)->int:
    if not isinstance(target_id, int):
        return 0
    repo = TargetScoreRepository()
    service_handler = TargetScoreService(target_score_repository=repo)
    
    try:
        return service_handler.calculate_activity_score_use_case(target_id=target_id)
    except Exception as e:
        logger.error(e)
        return 0
    

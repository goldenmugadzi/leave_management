from django import template
from ..services.kra import TargetScoreService, ActivityService
from ..repository.kra import TargetScoreRepository, KraActivityRepository
from loguru import logger
from loguru import logger
register = template.Library()

@register.filter
def get_activity_rating(activity_id)->int:
    if not isinstance(activity_id, int):
        logger.error(f"Invalid type for activity_id: Expected int, got {type(activity_id).__name__}")
        return 0
    
    repo = TargetScoreRepository()
    service_handler = TargetScoreService(target_score_repository=repo)
    
    try:
        return service_handler.calculate_activity_rating_score_use_case(activity_id=activity_id)
    except Exception as e:
        logger.error(f"Activity Score Rating Calculation, failed with error: {e}")
        return 0
    
@register.filter
def get_activity_weighted_score(activity_id)->float:
    if not isinstance(activity_id, int):
        logger.error(f"[Activity pk: {activity_id}] Invalid type for activity_id: Expected int, got {type(activity_id).__name__}")
        return 0.0

    repo = TargetScoreRepository()
    service_handler = TargetScoreService(target_score_repository=repo)
    weighted_score = service_handler.calculate_activity_weighted_score(activity_id=activity_id)
    try:
        return f"{weighted_score:.2f}"
    except Exception as e:
        logger.error(f"Activity weighted score Calculation, failed with error: {e}")
        return 0.0
    
@register.filter
def get_activity_actual_variance(activity_id)->float:
    if not isinstance(activity_id, int):
        logger.error(f"[Activity pk: {activity_id}] Invalid type for activity_id: Expected int, got {type(activity_id).__name__}")
        return 0.0

    repo = TargetScoreRepository()
    service_handler = TargetScoreService(target_score_repository=repo)
    
    try:
        return service_handler.calculate_actual_variance_use_case(score_object=repo.get_by_activity_id(activity_id=activity_id))
    except Exception as e:
        logger.error(f"Activity weighted score Calculation, failed with error: {e}")
        return 0.0
    

    
@register.filter
def get_kra_average_weighted_score(kra_id)->float:
    if not isinstance(kra_id, int):
        logger.error(f"[KRA pk: {kra_id}] Invalid type for kra_id: Expected int, got {type(kra_id).__name__}")
        return 0.0

    repo = KraActivityRepository()
    service_handler = ActivityService(activity_repo=repo)
    target_score_repo = TargetScoreRepository()
    target_score_service_handler = TargetScoreService(target_score_repository=target_score_repo)
    
    try:
        return service_handler.calculate_weighted_score_per_kra(kra_id=kra_id, target_score_service_object=target_score_service_handler)
    except Exception as e:
        logger.error(e)
        return 0.0
    
@register.filter
def get_target_score_by_activity_id(activity_id)->float:
    if not isinstance(activity_id, int):
        logger.error(f"[KRA pk: {activity_id}] Invalid type for kra_id: Expected int, got {type(activity_id).__name__}")
        return 0.0

    target_score_repo = TargetScoreRepository()
    score_obj = target_score_repo.get_by_activity_id(activity_id=activity_id)
    try:
        return score_obj.score
    except Exception as e:
        logger.error(e)
        return 0.0
    


from django import template
from ..services.kra import TargetScoreService, ActivityService, PerformanceDimensionService
from ..repository.kra import TargetScoreRepository, KraActivityRepository, PerformanceDimensionRepository
from loguru import logger

register = template.Library()

@register.filter
def get_performance_dimension_rating(performance_dimension_id)->int:
    if not isinstance(performance_dimension_id, int):
        logger.error(f"Invalid type for performance_dimension_id: Expected int, got {type(performance_dimension_id).__name__}")
        return 0
    
    try:
        repo = TargetScoreRepository()
        service_handler = TargetScoreService(target_score_repository=repo)
        score_obj = service_handler.target_score_repository.get_by_performance_dimension_id(performance_dimension_id=performance_dimension_id)
        return service_handler.calculate_performance_dimension_rating_score_use_case(score_object=score_obj)
    except Exception as e:
        logger.error(f"Activity Score Rating Calculation, failed with error: {e}")
        return 0
    
@register.filter
def get_performance_dimension_weighted_score(performance_dimension_id)->float:
    if not isinstance(performance_dimension_id, int):
        logger.error(f"[performance_dimension pk: {performance_dimension_id}] Invalid type for performance_dimension_id: Expected int, got {type(performance_dimension_id).__name__}")
        return 0.0

    try:
        repo = TargetScoreRepository()
        service_handler = TargetScoreService(target_score_repository=repo)
        weighted_score = service_handler.calculate_performance_dimension_weighted_score(performance_dimension_id=performance_dimension_id)
        return f"{weighted_score:.2f}"
    except Exception as e:
        logger.error(f"performance dimension weighted score Calculation, failed with error: {e}")
        return 0.0
    
@register.filter
def get_performance_dimension_actual_variance(performance_dimension_id)->float:
    if not isinstance(performance_dimension_id, int):
        logger.error(f"[performance_dimension pk: {performance_dimension_id}] Invalid type for performance_dimension_id: Expected int, got {type(performance_dimension_id).__name__}")
        return 0.0

    repo = TargetScoreRepository()
    service_handler = TargetScoreService(target_score_repository=repo)
    
    try:
        return service_handler.calculate_actual_variance_use_case(score_object=repo.get_by_performance_dimension_id(performance_dimension_id=performance_dimension_id))
    except Exception as e:
        logger.error(f"performance dimension weighted score Calculation, failed with error: {e}")
        return 0.0
    
@register.filter
def get_activity_total_score(activity_id)->float:
    if not isinstance(activity_id, int):
        logger.error(f"[Activity pk: {activity_id}] Invalid type for activity_id: Expected int")
        return 0.0

    try:        
        target_score_service_handler = TargetScoreService(target_score_repository=TargetScoreRepository())
        perf_dimension_service = PerformanceDimensionService(repo=PerformanceDimensionRepository())
        total_score = perf_dimension_service.calculate_total_performance_dimensions_weighted_score_per_activity(activity_id=activity_id, target_score_object=target_score_service_handler)
        return f"{total_score:.2f}"
    except Exception as e:
        logger.error(e)
        return 0.0

    
@register.filter
def get_kra_total_score(appraisal_kra_id)->float:
    if not isinstance(appraisal_kra_id, int):
        logger.error(f"[KRA pk: {appraisal_kra_id}] Invalid type for appraisal_kra_id: Expected int, got {type(appraisal_kra_id).__name__}")
        return 0.0

    try:
        repo = KraActivityRepository()
        activity_service_handler = ActivityService(activity_repo=repo)
        target_score_repo = TargetScoreRepository()
        target_score_service_handler = TargetScoreService(target_score_repository=target_score_repo)
        total_score = activity_service_handler.calculate_total_activities_weighted_scores_per_appraisal_kra(appraisal_kra_id=appraisal_kra_id, target_score_service_object=target_score_service_handler, performance_dimension_repo=PerformanceDimensionRepository())
        return f"{total_score:.2f}"
    except Exception as e:
        logger.error(e)
        return 0.0
    
@register.filter
def get_target_score_by_performance_dimension_id(performance_dimension_id)->float:
    if not isinstance(performance_dimension_id, int):
        logger.error(f"[performance_dimension pk: {performance_dimension_id}] Invalid type for kra_id: Expected int, got {type(performance_dimension_id).__name__}")
        return 0.0

    try:
        target_score_repo = TargetScoreRepository()
        score_obj = target_score_repo.get_by_performance_dimension_id(performance_dimension_id=performance_dimension_id)
        return score_obj.score
    except Exception as e:
        logger.error(e)
        return 0.0
    


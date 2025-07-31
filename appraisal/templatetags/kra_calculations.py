from django import template

from ..repository.kra import AppraisalOutPutPerformanceDimensionScoreRepository
from ..services.kra import AppraisalScoreDimensionService
from ..models.kra import AppraisalOutPutPerformanceDimensionScore

from loguru import logger

register = template.Library()

def appraisal_performance_dimension_handler(performance_dimension_id: int)->int|AppraisalScoreDimensionService:
    repo = AppraisalOutPutPerformanceDimensionScoreRepository()
    score_object = repo.get_by_id(pk=performance_dimension_id)
    if score_object is None:
        return 1
    return AppraisalScoreDimensionService(score_object=score_object)


@register.filter
def get_performance_dimension_rating(performance_dimension_id)->int:
    
    try:
        performance_dimension_id = int(performance_dimension_id)
    except ValueError:
        logger.error(f"[KraCalculationTemplatetag] get_performance_dimension_rating(), appraisal performance dimension object with id: {performance_dimension_id}, Invalid type, Expected int, got {type(performance_dimension_id).__name__}")
        return 1
        
    try:
        service_handler = appraisal_performance_dimension_handler(performance_dimension_id=performance_dimension_id)
        if not isinstance(service_handler, AppraisalScoreDimensionService):
            logger.error(f"[KraCalculationTemplatetag] get_performance_dimension_rating(), appraisal performance dimension object with id: {performance_dimension_id}, not found")
            return service_handler
        return service_handler.calculate_performance_dimension_rating_score_use_case()
    except Exception as e:
        logger.error(f"[KraCalculationTemplatetag] get_performance_dimension_rating(), appraisal performance dimension object with id: {performance_dimension_id}, failed with error: {e}")
        return 1
    
@register.filter
def get_performance_dimension_weighted_score(performance_dimension_id)->float:
    
    try:
        performance_dimension_id = int(performance_dimension_id)
    except ValueError:
        logger.error(f"[KraCalculationTemplatetag] get_performance_dimension_weighted_score(), appraisal performance dimension object with id: {performance_dimension_id}, Invalid type Expected int, got {type(performance_dimension_id).__name__}")
        return 0.0

    try:
        service_handler = appraisal_performance_dimension_handler(performance_dimension_id=performance_dimension_id)

        if not isinstance(service_handler, AppraisalScoreDimensionService):
            logger.error(f"[KraCalculationTemplatetag] get_performance_dimension_weighted_score(), appraisal performance dimension object with id: {performance_dimension_id}, not found")
            return service_handler
        return service_handler.calculate_performance_dimension_weighted_score()
    except Exception as e:
        logger.error(f"[KraCalculationTemplatetag] get_performance_dimension_weighted_score(), appraisal performance dimension object with id: {performance_dimension_id}, failed with error: {e}")
        return 0.0
    
@register.filter
def get_performance_dimension_actual_variance(performance_dimension_id)->float:
    
    try:
        performance_dimension_id = int(performance_dimension_id)
    except ValueError:
        logger.error(f"[KraCalculationTemplatetag] get_performance_dimension_actual_variance(), appraisal performance dimension object with id: {performance_dimension_id}, Invalid type Expected int, got {type(performance_dimension_id).__name__}")
        return 0.0

        
    try:
        service_handler = appraisal_performance_dimension_handler(performance_dimension_id=performance_dimension_id)

        if not isinstance(service_handler, AppraisalScoreDimensionService):
            logger.error(f"[KraCalculationTemplatetag] get_performance_dimension_actual_variance(), appraisal performance dimension object with id: {performance_dimension_id}, not found")
            return service_handler
        return service_handler.calculate_actual_variance_use_case()
    except Exception as e:
        logger.error(f"[KraCalculationTemplatetag] get_performance_dimension_actual_variance(), appraisal performance dimension object with id: {performance_dimension_id}, failed with error: {e}")
        return 0.0
    
@register.filter
def get_activity_total_score(activity_id)->float:
    
    try:
        activity_id = int(activity_id)
    except ValueError:
        logger.error(f"[get_activity_total_score pk: {activity_id}] Invalid type Expected int, got {type(activity_id).__name__}")
        return 0.0

    try:        
        ...
    except Exception as e:
        logger.error(e)
        return 0.0

    
@register.filter
def get_kra_total_score(appraisal_kra_id)->float:
    
    try:
        appraisal_kra_id = int(appraisal_kra_id)
    except ValueError:
        logger.error(f"[get_kra_total_score pk: {appraisal_kra_id}] Invalid type Expected int, got {type(appraisal_kra_id).__name__}")
        return 0.0
    
    try:
        ...
    except Exception as e:
        logger.error(e)
        return 0.0
    
@register.filter
def get_target_score_by_performance_dimension_id(performance_dimension_id)->float:
    
    try:
        performance_dimension_id = int(performance_dimension_id)
    except ValueError:
        logger.error(f"[get_target_score_by_performance_dimension_id pk: {performance_dimension_id}] Invalid type Expected int, got {type(performance_dimension_id).__name__}")
        return 0.0

    try:
        ...
    except Exception as e:
        logger.error(e)
        return 0.0
    


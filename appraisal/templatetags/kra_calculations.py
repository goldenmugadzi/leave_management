from django import template

from loguru import logger

register = template.Library()

@register.filter
def get_performance_dimension_rating(performance_dimension_id)->int:
    
    try:
        performance_dimension_id = int(performance_dimension_id)
    except ValueError:
        logger.error(f"[get_performance_dimension_rating pk: {performance_dimension_id}] Invalid type, Expected int, got {type(performance_dimension_id).__name__}")
        return 0
        
    try:
        ...
    except Exception as e:
        logger.error(f"Activity Score Rating Calculation, failed with error: {e}")
        return 0
    
@register.filter
def get_performance_dimension_weighted_score(performance_dimension_id)->float:
    
    try:
        performance_dimension_id = int(performance_dimension_id)
    except ValueError:
        logger.error(f"[get_performance_dimension_weighted_score pk: {performance_dimension_id}] Invalid type Expected int, got {type(performance_dimension_id).__name__}")
        return 0.0

    try:
        ...
    except Exception as e:
        logger.error(f"performance dimension weighted score Calculation, failed with error: {e}")
        return 0.0
    
@register.filter
def get_performance_dimension_actual_variance(performance_dimension_id)->float:
    
    try:
        performance_dimension_id = int(performance_dimension_id)
    except ValueError:
        logger.error(f"[get_performance_dimension_actual_variance pk: {performance_dimension_id}] Invalid type Expected int, got {type(performance_dimension_id).__name__}")
        return 0.0

        
    try:
        ...
    except Exception as e:
        logger.error(f"performance dimension weighted score Calculation, failed with error: {e}")
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
    


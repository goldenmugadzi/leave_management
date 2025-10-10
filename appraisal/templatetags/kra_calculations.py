from django import template

from ..repository.kra import AppraisalOutPutPerformanceDimensionScoreRepository
from ..services.kra import AppraisalScoreDimensionService, AppraisalDepartmentOutputService


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
def get_output_total_score(output_id)->float:
    
    try:
        output_id = int(output_id)
    except ValueError:
        logger.error(f"[KraCalculationTemplatetag] get_output_total_score(), output object with id: {output_id}, Invalid type Expected int, got {type(output_id).__name__}")
        return 0.0

    try:
        service_handler = AppraisalDepartmentOutputService()
        total_weighted_score = service_handler.get_output_total_weighted_score(appraisal_dept_output_id=output_id, performance_dimension_repo=AppraisalOutPutPerformanceDimensionScoreRepository())
        return total_weighted_score
    except Exception as e:
        logger.error(f"[KraCalculationTemplatetag] get_output_total_score(), output object with id: {output_id}, failed with error: {e}")
        return 0.0


@register.filter
def get_department_objective_total_score(department_objective_id: int)->float:
    
    try:
        department_objective_id = int(department_objective_id)
    except ValueError:
        logger.error(f"[KraCalculationTemplatetag] get_department_objective_total_score(), department_objective object with id: {department_objective_id}, Invalid type Expected int, got {type(department_objective_id).__name__}")
        return 0.0

    try: 
        service_handler = AppraisalDepartmentOutputService()
        total_weighted_score = service_handler.get_department_objective_total_weighted_score(department_objective_id=department_objective_id, performance_dimension_repo=AppraisalOutPutPerformanceDimensionScoreRepository())
        return total_weighted_score
    except Exception as e:
        logger.error(f"[KraCalculationTemplatetag] get_department_objective_total_score(), output object with id: {department_objective_id}, failed with error: {e}")
        return 0.0
    

@register.simple_tag
def get_department_objectives_total_year_quarter_weighted_score(year_quarter_id: int, appraisal_id: int)->float:
    
    try:
        year_quarter_id = int(year_quarter_id)
        appraisal_id = int(appraisal_id)
    except ValueError:
        logger.error(f"[KraCalculationTemplatetag] get_department_objectives_total_year_quarter_weighted_score(), quarter with id: {year_quarter_id}, appraisal with id: {appraisal_id}, Invalid type Expected int, got {type(year_quarter_id).__name__}")
        return 0.0

    try: 
        service_handler = AppraisalDepartmentOutputService()
        total_weighted_score = service_handler.get_department_objectives_total_year_quarter_weighted_score(year_quarter_id=year_quarter_id, appraisal_id=appraisal_id, performance_dimension_repo=AppraisalOutPutPerformanceDimensionScoreRepository())
        return total_weighted_score
    except Exception as e:
        logger.error(f"[KraCalculationTemplatetag] get_department_objectives_total_year_quarter_weighted_score(), quarter with id: {year_quarter_id}, appraisal with id: {appraisal_id}, failed with error: {e}")
        return 0.0
    


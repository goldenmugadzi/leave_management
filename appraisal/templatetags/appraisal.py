from django import template
from ..helpers.getters.sections import SectionsStagesHandler
from ..repository.appraisal import AppraisalRepository
from ..repository.kra import ScoreDocumentRepository
from loguru import logger

register = template.Library()

@register.filter
def get_appraisal_sections(appraisal_id: int):
    if not isinstance(appraisal_id, int):
        logger.error(f"[get_appraisal_sections()] templatetags, Invalid type for appraisal_id: Expected int, got {type(appraisal_id).__name__}")

    try:
        sections_handler = SectionsStagesHandler()
        data =  sections_handler.get_sections_with_urls()
        data.pop() # removes the last section 6 which is not applicable
    
        appraisal_obj = AppraisalRepository().get_appraisal_by_pk(appraisal_id=appraisal_id)
        if appraisal_obj.is_accepted:
            return data
        return data[:1]
    except Exception as e:
        logger.error(f"[get_appraisal_sections()] templatetags with appraisal_id; {appraisal_id}, failed with error: {e}")
        return []

@register.filter
def get_perf_dimension_supporting_docs(perf_dimension_id: int):
    if not isinstance(perf_dimension_id, int):
        logger.error(f"[get_perf_dimension_supporting_docs()] templatetags, Invalid type for perf_dimension_id: Expected int, got {type(perf_dimension_id).__name__}")

    try:
        repo = ScoreDocumentRepository()
        return repo.fetch_by_score_id(score_obj_id=perf_dimension_id)
    except Exception as e:
        logger.error(f"[get_perf_dimension_supporting_docs()] templatetags with perf_dimension_id; {perf_dimension_id}, failed with error: {e}")
        return []


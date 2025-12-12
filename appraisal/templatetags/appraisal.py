from django import template
from ..helpers.getters.sections import SectionsStagesHandler
from ..repository.appraisal import AppraisalRepository
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
        if appraisal_obj.reviewer:
            return data
        return data[:1]
    except Exception as e:
        logger.error(f"[get_appraisal_sections()] templatetags with appraisal_id; {appraisal_id}, failed with error: {e}")
        return []
    
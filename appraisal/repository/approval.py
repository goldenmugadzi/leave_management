from typing import List
from django.db.models.query import QuerySet
from ..models import AppraisalWorkflow, Appraisal
from loguru import logger

class AppraisalWorkflowRepository:
    def retrieve_by_appraisal(self, appraisal: Appraisal)->QuerySet[AppraisalWorkflow]:
        try:
            return AppraisalWorkflow.objects.filter(appraisal=appraisal).order_by('stage_num')
        except Exception as e:
            raise Exception(f"AppraisalWorkflowRepository retrieve_by_appraisal failed with error: {e}")
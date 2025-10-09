from typing import List
from django.db.models.query import QuerySet
from ..models import AppraisalWorkflow, AppraisalApprovalWorkFlowQuarter
from it.users.models import UserProfile
from ..models.helpers import YearQuarter
from loguru import logger

class AppraisalWorkflowRepository:
    def retrieve_by_appraisal(self, appraisal_id: int)->QuerySet[AppraisalWorkflow]:
        try:
            return AppraisalWorkflow.objects.filter(appraisal__id=appraisal_id).order_by('stage_num')
        except Exception as e:
            raise Exception(f"AppraisalWorkflowRepository retrieve_by_appraisal failed with error: {e}")
        
    def update(self, workflow_object: AppraisalWorkflow, is_completed: bool, updated_by: UserProfile)->AppraisalWorkflow:
        is_update = False
        
        try:
            if workflow_object.is_completed != is_completed:
                workflow_object.is_completed = is_completed
                is_update = True
            
            if workflow_object.updated_by != updated_by:
                workflow_object.updated_by = updated_by
                is_update = True
            
            if is_update:
                workflow_object.save()
            return workflow_object
        except Exception as e:
            raise Exception(f"AppraisalWorkflowRepository update handler failed with error: {e}")


class AppraisalApprovalWorkFlowQuarterRepository:
    def create(self, appraisal_workflow_obj: AppraisalWorkflow, year_quarter_obj: YearQuarter)->AppraisalApprovalWorkFlowQuarter:
        try:
            return AppraisalApprovalWorkFlowQuarter.objects.create(
                appraisal_workflow=appraisal_workflow_obj,
                year_quarter = year_quarter_obj
            )
        except Exception as e:
            raise Exception(f"[AppraisalApprovalWorkFlowQuarterRepository] create repo with appraisal_workflow pk: {appraisal_workflow_obj.id}, failed with error: {e}")

from typing import List
from django.db.models.query import QuerySet
from ..models import AppraisalWorkflow, AppraisalApprovalWorkFlowQuarter
from it.users.models import UserProfile
from ..models.helpers import YearQuarter
from loguru import logger

class AppraisalWorkflowRepository:
    def bulk_create(self, appraisal_workflow_list: List[AppraisalWorkflow])->bool:
        try:
            AppraisalWorkflow.objects.bulk_create(
                objs=appraisal_workflow_list,
            )
            return True
        except Exception as e:
            raise Exception(f"AppraisalWorkflowRepository bulk create failed with error: {e}")

    def retrieve_by_appraisal(self, appraisal_id: int)->QuerySet[AppraisalWorkflow]:
        try:
            return AppraisalWorkflow.objects.filter(appraisal__id=appraisal_id).order_by('stage_num')
        except Exception as e:
            raise Exception(f"AppraisalWorkflowRepository retrieve_by_appraisal failed with error: {e}")
    
    def get_by_id(self, appraisal_workflow_id: int)->AppraisalWorkflow:
        try:
            objs = AppraisalWorkflow.objects.filter(id=appraisal_workflow_id)
            return objs.first()
        except Exception as e:
            raise Exception(f"AppraisalWorkflowRepository get_by_id by pk: {appraisal_workflow_id}, failed with error: {e}")
    
    def fetch_by_appraisal_id(self, appraisal_id: int)->List[AppraisalWorkflow]:
        try:
            return AppraisalWorkflow.objects.filter(appraisal__id=appraisal_id)
        except Exception as e:
            raise Exception(f"AppraisalWorkflowRepository fetch_by_appraisal_id by pk: {appraisal_id}, failed with error: {e}")
        
    def fetch_by_appraisal_id_quarter_id(self, appraisal_id: int, year_quarter_id: int)->List[AppraisalWorkflow]:
        try:
            return AppraisalWorkflow.objects.filter(appraisal__id=appraisal_id, year_quarter__id=year_quarter_id)
        except Exception as e:
            raise Exception(f"AppraisalWorkflowRepository fetch_by_appraisal_id_quarter_id by appraisal pk: {appraisal_id} and year quarter pk: {year_quarter_id}, failed with error: {e}")
        
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

    def get_by_approval_workflow_quarter_id(self, appraisal_workflow_id: int, quarter_id: int)->AppraisalApprovalWorkFlowQuarter:
        try:
            qr = AppraisalApprovalWorkFlowQuarter.objects.filter(appraisal_workflow__id=appraisal_workflow_id, year_quarter__id=quarter_id)
            return qr.first()
        except Exception as e:
            raise Exception(f"[AppraisalApprovalWorkFlowQuarterRepository] get_by_approval_workflow_quarter_id repo with appraisal_workflow pk: {appraisal_workflow_id} and year quarter id: {quarter_id}, failed with error: {e}")

    def approved_stage_completed(self, quarterly_appraisal_workflow_obj: AppraisalApprovalWorkFlowQuarter, is_complete: bool)->AppraisalApprovalWorkFlowQuarter:
        try:
            is_changed = False
            if quarterly_appraisal_workflow_obj.is_complete != is_complete:
                quarterly_appraisal_workflow_obj.is_complete = is_complete
                is_changed = True
            
            if is_changed:
                quarterly_appraisal_workflow_obj.save()
            return quarterly_appraisal_workflow_obj
        except Exception as e:
            raise Exception(f"[AppraisalApprovalWorkFlowQuarterRepository] approved_stage_completed repo with appraisal_workflow_quarter pk: {quarterly_appraisal_workflow_obj.id}, failed with error: {e}")

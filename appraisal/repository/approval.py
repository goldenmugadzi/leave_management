from typing import List
from django.db.models.query import QuerySet
from ..models import AppraisalWorkflow, AppraisalKraReviewerStatus
from it.users.models import UserProfile
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

class AppraisalKraReviewerStatusRepository:
    def retrieve_by_appraisal_kra_id(self, appraisal_kra_id: int)->AppraisalKraReviewerStatus:
        try:
            qr = AppraisalKraReviewerStatus.objects.filter(appraisal_kra__id=appraisal_kra_id)
            if not qr.exists():
                raise Exception("AppraisalKraReviewerStatus object not found")
            return qr.first()
        except Exception as e:
            raise Exception(f"[AppraisalKraReviewerStatusRepository] retrieve_by_appraisal_kra_id failed with error: {e}")
       
    def retrieve_by_appraisal_kra_year_quarter_id(self, year_quarter_obj_id: int)->QuerySet[AppraisalKraReviewerStatus]:
        try:
            return AppraisalKraReviewerStatus.objects.filter(appraisal_kra__quarter__id=year_quarter_obj_id)

        except Exception as e:
            raise Exception(f"[AppraisalKraReviewerStatusRepository] retrieve_by_appraisal_kra_year_quarter_id failed with error: {e}")
       
from dataclasses import dataclass
from ..repository.approval import AppraisalWorkflowRepository
from ..helpers.types.approval import AppraisalWorkflowDataType

class AppraisalWorkflowErr(Exception):
    pass


@dataclass
class AppraisalWorkflowService:
    repo: AppraisalWorkflowRepository
    
    def fetch_by_appraisal_id(self, appraisal_id: int)->AppraisalWorkflowDataType:
        try:
            qr = self.repo.retrieve_by_appraisal(appraisal_id=appraisal_id)
            last_stg_num = qr.last().stage_num
            data = AppraisalWorkflowDataType(
                stages=qr,
                last_stage_number=last_stg_num
            )
            return data
        except Exception as e:
            raise AppraisalWorkflowErr(f"AppraisalWorkflowService fetch_by_appraisal_id, failed with error: {e}")
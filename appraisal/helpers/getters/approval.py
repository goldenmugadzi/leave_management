from dataclasses import dataclass
from typing import Protocol, List
from ...repository.approval import AppraisalWorkflowRepository
from ..types.quarters import ApprovedQuartersType
from loguru import logger


@dataclass
class ApprovalStagesHandler:
    appraisal_id: int
    
    def get_approval_queryset(self):
        """Retrieve all approval workflow stages for the given appraisal."""
        approval_workflow_repo = AppraisalWorkflowRepository()
        return approval_workflow_repo.retrieve_by_appraisal(appraisal_id=self.appraisal_id)

    def get_completed_approval_queryset(self):
        """Retrieve completed approval stages."""
        qr = self.get_approval_queryset()
        return qr.filter(is_completed=True) if qr else None
    
    def get_uncompleted_approval_queryset(self):
        """Retrieve uncompleted approval stages."""
        qr = self.get_approval_queryset()
        return qr.filter(is_completed=False) if qr else None
    
    def __get_next_stage_obj__(self, current_stage_num: int):
        """Retrieve the next approval stage based on the current stage number."""
        qr = self.get_approval_queryset()
        next_stage_qr = qr.filter(stage_num__gt=current_stage_num) if qr.exists() else None
        return next_stage_qr.first() if next_stage_qr and next_stage_qr.exists() else None
    
    def get_current_and_next_stage(self):
        """Determine the current and next approval stages."""
        completed_qr = self.get_completed_approval_queryset()
        uncompleted_qr = self.get_uncompleted_approval_queryset()

        data = {"current_stage": None, "next_stage": None}

        if completed_qr and completed_qr.exists():
            current_stage_obj = completed_qr.last()
            data["current_stage"] = current_stage_obj
            data["next_stage"] = self.__get_next_stage_obj__(current_stage_obj.stage_num)
            return data
        if uncompleted_qr and uncompleted_qr.exists():
            current_stage_obj = uncompleted_qr.first()
            data["current_stage"] = current_stage_obj
            data["next_stage"] = self.__get_next_stage_obj__(current_stage_obj.stage_num)
            return data
        
        return data

    
    def get_stages_info(self):
        """Retrieve all stages along with current and next stage information."""
        qr = self.get_approval_queryset()
        last_stage_number = qr.last().stage_num if qr and qr.exists() else None

        return {
            "stages": qr,
            "last_stage_number": last_stage_number,
            **self.get_current_and_next_stage()
        }


# Strategy Pattern use Protocol for composition rather inheritance
class ApprovalWorkflowQuarterStagesStrategyInterface(Protocol):
    def get_approved_quarters(self, appraisal_kra_id: int)->List[ApprovedQuartersType]:
        """handler that retrieve all quarters[1,2,3,4] approval status.

        Args:
            appraisal_kra_id (int): AppraisalKra pk

        Returns:
            ApprovedQuartersType: pydantic type for with all quarters[1,2,3,4]
        """
        pass
        

    

class ApprovalWorkflowQuarterStagesStrategyContext:
    def __init__(self, strategy: ApprovalWorkflowQuarterStagesStrategyInterface):
        self.strategy = strategy
        
    def get_stage_quarters_approval(self, appraisal_kra_id: int)->List[ApprovedQuartersType]:
        try:
            return self.strategy.get_approved_quarters(appraisal_kra_id=appraisal_kra_id)
        except Exception as e:
            logger.warning(f"[ApprovalWorkflowQuarterStagesStrategyInterface] for {self.strategy.__class__()}, failed with error: {e}")
            return None
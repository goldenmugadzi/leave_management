from pydantic import BaseModel
from enum import Enum
from ...models import AppraisalWorkflow


class AppraisalWorkflowDataType(BaseModel):
    stages: list
    last_stage_number: int
    

class ApprovalStageChoices(Enum):
    First_Quarter = "First Quarter"
    Second_Quarter = "Second Quarter"
    Third_Quarter = "Third Quarter"
    Fourth_Quarter = "Fourth Quarter"

    @classmethod
    def choices(cls):
        return [(choice.value, choice.name.replace("_", " ").title()) for choice in cls]


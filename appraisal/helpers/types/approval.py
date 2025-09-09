from pydantic import BaseModel
from ...models import AppraisalWorkflow


class AppraisalWorkflowDataType(BaseModel):
    stages: list
    last_stage_number: int
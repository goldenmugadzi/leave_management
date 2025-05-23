from pydantic import BaseModel

class ApprovedQuartersType(BaseModel):
    appraisal_kra_id: int
    quarter_name: str
    is_approved: bool
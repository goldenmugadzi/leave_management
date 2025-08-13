from pydantic import BaseModel

class ApprovedQuartersType(BaseModel):
    appraisal_kra_id: int
    quarter_name: str
    is_approved: bool
    
class CurrentQuartersType(BaseModel):
    is_within_first_quarter: bool
    is_within_second_quarter: bool
    is_within_third_quarter: bool
    is_within_fourth_quarter: bool
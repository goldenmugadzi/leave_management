from pydantic import BaseModel

class ApprovedQuartersType(BaseModel):
    quarter_name: str
    is_approved: bool
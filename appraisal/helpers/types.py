from typing import List, Dict, Optional, Any
from pydantic import BaseModel

class AppraisalPayloadType(BaseModel):
    experiences: Optional[List[Dict[str, Any]]] = None
    appraisal_experiences: Optional[List[Dict[str, Any]]] = None
    qualifications: Optional[List[Dict[str,Any]]] = None
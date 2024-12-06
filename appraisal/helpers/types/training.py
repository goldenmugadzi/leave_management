from typing import List, Optional
from pydantic import BaseModel, Field


class CompetencyType(BaseModel):
    name: str = Field(..., description="The competency name of the job.")
    
class InterventionStrategy(BaseModel):
    description: str = Field(..., description="The description of intervention strategy.")
    category: str = Field(..., description="The category of intervention strategy.")
    
    
class TrainingAndDevelopment(BaseModel):
    required_competencies: Optional[List[CompetencyType]] = Field(..., description="The list of required competencies")
    competency_gaps: Optional[List[CompetencyType]] = Field(..., description="The list of competency gaps")
    intervention_strategies: Optional[List[InterventionStrategy]] = Field(..., description="The list of intervention strategies")
    action_recommended: Optional[str] = Field(..., description="The description of action recommended.")
    action_taken: Optional[str] = Field(..., description="The description of action taken.")

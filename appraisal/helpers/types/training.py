from typing import List, Optional
from pydantic import BaseModel, Field


class CompetencyType(BaseModel):
    id: int = Field(..., description="The ID of the competency.")
    

class InterventionStrategyType(BaseModel):
    description: str = Field(..., description="The description of intervention strategy.")
    category: str = Field(..., description="The category of intervention strategy.")


class TrainingAndDevelopmentCreateUpdateType(BaseModel):
    existence_competencies: Optional[List[CompetencyType]] = Field(..., description="The list of required competencies")
    intervention_strategies: Optional[List[InterventionStrategyType]] = Field(..., description="The list of intervention strategies")
    action_recommended: Optional[str] = Field(..., description="The description of action recommended.")
    action_taken: Optional[str] = Field(..., description="The description of action taken.")

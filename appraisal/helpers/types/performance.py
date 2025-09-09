from typing import List, Optional
from pydantic import BaseModel, Field

class StrengthAndWeaknessTypes(BaseModel):
    """
    Represents a strength or weakness type, such as specific skills or areas of improvement.

    Attributes:
        name (str): The name of the strength or weakness (e.g., "Teamwork", "Time Management").
    """
    name: str = Field(..., description="The name of strength or weakness.")


class PerformanceReviewType(BaseModel):
    """
    Represents a performance review for a particular quarter of the year, including strengths and weaknesses.

    Attributes:
        strength (Optional[List[StrengthAndWeaknessTypes]]): A list of strengths identified in the performance review.
        weakness (Optional[List[StrengthAndWeaknessTypes]]): A list of weaknesses identified in the performance review.
    """
    strength: Optional[List[StrengthAndWeaknessTypes]] = Field(None, description="The list of strengths")
    weakness: Optional[List[StrengthAndWeaknessTypes]] = Field(None, description="The list of weaknesses")

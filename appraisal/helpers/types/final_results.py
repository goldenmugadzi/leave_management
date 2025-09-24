from pydantic import BaseModel, Field, field_validator
from decimal import Decimal
from typing import Annotated
from datetime import date
from enum import Enum

class QuartersNames(Enum):
    first_quarter = "First Quarter"
    second_quarter = "Second Quarter"
    third_quarter = "Third Quarter"
    fourth_quarter = "Fourth Quarter"



class FinalRatingType(BaseModel):
    name: str = Field(..., description="The quarter name.")
    start_date: date = Field(..., description="The start date of the quarter.")
    end_date: date = Field(..., description="The end date of the quarter.")
    total_score: Annotated[Decimal, Field(max_digits=5, decimal_places=2)] = Field(
        ..., description="Quarterly total score."
    )
    
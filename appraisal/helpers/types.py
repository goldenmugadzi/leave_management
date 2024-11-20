from typing import List, Optional
from pydantic import BaseModel, Field
from django.core.files.uploadedfile import UploadedFile


class QualificationsType(BaseModel):
    """
    Represents a qualification with an optional file.

    Attributes:
        name (str): The name of the qualification.
        file (Optional[UploadedFile]): The associated file for the qualification. Optional.
    """
    name: str = Field(..., description="The name of the qualification.")
    file: Optional[UploadedFile] = Field(None, description="The uploaded file object associated with the qualification.")

    class Config:
        arbitrary_types_allowed = True

class ExperienceType(BaseModel):
    """
    Represents an experience detail.

    Attributes:
        name (str): The name of the skill or experience.
        years_of_experience (int): Years of experience (non-negative).
        months_of_experience (int): Months of experience (0-11).
    """
    name: str = Field(..., description="The name of the skill or experience.")
    years_of_experience: int = Field(..., ge=0, description="Years of experience (non-negative).")
    months_of_experience: int = Field(..., ge=0, lt=12, description="Months of experience (0-11).")

class AppraisalPayloadType(BaseModel):
    """
    Represents the payload structure for an appraisal request.

    Attributes:
        experiences (Optional[List[ExperienceType]]): 
            A list of experience details, where each entry includes information 
            about a specific experience such as the name, years of experience, 
            and months of experience. This field is optional.
            
        qualifications (Optional[List[QualificationsType]]): 
            A list of qualifications, where each qualification includes 
            details such as the name and an optional file associated with it. 
            This field is optional.
    """
    experiences: Optional[List[ExperienceType]] = Field(None, description="A list of experience details.")
    qualifications: Optional[List[QualificationsType]] = Field(None, description="A list of qualifications.")

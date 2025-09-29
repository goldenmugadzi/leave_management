from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from django.core.files.uploadedfile import UploadedFile
from ...models import KeyResultArea, AppraisalOutPutPerformanceDimensionScore, DepartmentObjective, TrainingAndDevelopment, PerformanceProgressReview, AppraiseePersonalAttribute, Appraisal
from it.users.models import Designations, Regions, Sections
from ..types.final_results import FinalRatingType

class QualificationsType(BaseModel):
    """
    Represents a qualification with an optional file.

    Attributes:
        name (str): The name of the qualification.
        file (Optional[UploadedFile]): The associated file for the qualification. Optional.
    """
    name: str = Field(..., description="The name of the qualification.")
    file: Optional[UploadedFile] = Field(None,
                                         description="The uploaded file object associated with the qualification.")

    model_config = ConfigDict(arbitrary_types_allowed=True)


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

class AppraisalPersonalDetails(BaseModel):
    appraisee_name: str
    appraisee_position: Designations|None
    appraisee_qualifications: List[str]
    appraisee_experiance: List[str]
    appraisee_national_id: str|None
    appraisee_ec_no: str
    appraisee_date_of_appointment: str|None
    appraisee_position_appointment_date: str|None
    appraisee_department: Sections|None
    appraisee_station: Regions|None
    appraiser_name: str
    appraiser_position: Designations|None
    reviewer_name: str
    reviewer_position: Designations|None
    
    model_config = ConfigDict(arbitrary_types_allowed=True)

class AppraisalDepartmentObjectivesDependencies(BaseModel):
    department_objective: DepartmentObjective
    quarter: int
    total_outputs: int
    appraisal_dept_outputs: List[AppraisalOutPutPerformanceDimensionScore]
    
    model_config = ConfigDict(arbitrary_types_allowed=True)

class AppraisalPerformanceAssessmentType(BaseModel):
    kra: KeyResultArea
    total_objectives: int
    appraisal_departmental_dep: List[AppraisalDepartmentObjectivesDependencies]
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
class TrainingAndDevType(BaseModel):
    quarter: int
    quarter_training_dev: TrainingAndDevelopment
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
class PerformanceProgressReviewType(BaseModel):
    quarter: int
    perf_progress_review: PerformanceProgressReview
    
    model_config = ConfigDict(arbitrary_types_allowed=True)

class FinalScoreType(BaseModel):
    final_score: float
    rating: FinalRatingType

class FinalPerformanceAssType(BaseModel):
    final_score: FinalScoreType
    personal_attributes: List[AppraiseePersonalAttribute]
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
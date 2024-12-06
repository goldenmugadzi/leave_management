from typing import List
from dataclasses import dataclass
from ..models import AppraisalExperience
from ..repository import AppraisalExperienceRepository

@dataclass
class AppraisalExperienceService:
    appraisal_repo: AppraisalExperienceRepository
    def get_by_appraisal_id_use_case(self, appraisal_id)->List[AppraisalExperience]:
        return self.appraisal_repo.get_experiences_by_appraisal_id(appraisal_id=appraisal_id)
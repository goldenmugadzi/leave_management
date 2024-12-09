from dataclasses import dataclass
from appraisal.models import TrainingAndDevelopment

from appraisal.models.appraisal import Appraisal
from ..repository.training import TrainingAndDevelopmentRepository
from ..helpers.types.training import TrainingAndDevelopmentCreateUpdateType

class TrainingAndDevelopmentServiceErr(Exception):
    ...

@dataclass
class TrainingAndDevelopmentService:
    training_dev_repo: TrainingAndDevelopmentRepository

    def create_use_case(self, appraisal_object: Appraisal, quarter: int)->TrainingAndDevelopment:
        try:

            return self.training_dev_repo.create(appraisal_object=appraisal_object, quarter=quarter)
        except Exception as e:
            raise TrainingAndDevelopmentServiceErr(f"Failed to create training and development with error: {e}")

    def update_use_case(self, training_development_object: TrainingAndDevelopment, quarter: int, payload: TrainingAndDevelopmentCreateUpdateType)->TrainingAndDevelopment:
        try:
            return self.training_dev_repo.update(training_development_object=training_development_object, quarter=quarter, data=payload)
        except Exception as e:
            raise TrainingAndDevelopmentServiceErr(f"Failed to update training and development with error: {e}")

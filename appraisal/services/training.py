from dataclasses import dataclass

from appraisal.models.appraisal import Appraisal
from ..repository.training import TrainingAndDevelopmentRepository

class TrainingAndDevelopmentServiceErr(Exception):
    ...

@dataclass
class TrainingAndDevelopmentService:
    training_dev_repo: TrainingAndDevelopmentRepository

    def create_use_case(self, appraisal_object: Appraisal, quarter: int):
        try:

            return self.training_dev_repo.create(appraisal_object=appraisal_object, quarter=quarter)
        except Exception as e:
            raise TrainingAndDevelopmentServiceErr(f"Failed to create training and development with error: {e}")

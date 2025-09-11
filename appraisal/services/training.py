from typing import List
from dataclasses import dataclass
from appraisal.models import TrainingAndDevelopment

from appraisal.models.appraisal import Appraisal
from ..repository.training import TrainingAndDevelopmentRepository
from ..helpers.types.training import TrainingAndDevelopmentCreateUpdateType
from ..models.helpers import YearQuarter
from django.db import transaction
from loguru import logger

class TrainingAndDevelopmentServiceErr(Exception):
    ...

@dataclass
class TrainingAndDevelopmentService:
    training_dev_repo: TrainingAndDevelopmentRepository

    def create_use_case(self, appraisal_object: Appraisal, quarter_obj: YearQuarter)->TrainingAndDevelopment:
        try:

            return self.training_dev_repo.create(appraisal_object=appraisal_object, quarter_obj=quarter_obj)
        except Exception as e:
            raise TrainingAndDevelopmentServiceErr(f"Failed to create training and development with error: {e}")

    def create_for_all_quarters(self, appraisal_object: Appraisal, year_quarter_qr: List[YearQuarter])->None:
        try:
            training_development_repo_handler = TrainingAndDevelopmentRepository()
            training_development_service_handler = TrainingAndDevelopmentService(training_dev_repo=training_development_repo_handler)

            with transaction.atomic():
                for year_quarter_obj in year_quarter_qr:
                    logger.info(f"[ TrainingAndDevelopmentService ]: create with year obj {year_quarter_obj} for user id: {appraisal_object.user.id} and appraisal pk: {appraisal_object.id} ....")
                    try:
                        training_development_service_handler.create_use_case(
                            appraisal_object=appraisal_object,
                            quarter_obj=year_quarter_obj
                        )
                        logger.success(f"[ TrainingAndDevelopmentService ]: year obj {year_quarter_obj} for user id: {appraisal_object.user.id} and appraisal pk: {appraisal_object.id} created successfully")
                    except Exception as e:
                        raise Exception(f"creation handler, year obj {year_quarter_obj} for user id: {appraisal_object.user.id} and appraisal pk: {appraisal_object.id}, failed with error: {e}")
        except Exception as e:
            logger.error(f"[TrainingAndDevelopmentService]: creating training and development for appraisal pk: {appraisal_object.id}, with error: {e} ")

    
    def update_use_case(self, training_development_object: TrainingAndDevelopment, payload: TrainingAndDevelopmentCreateUpdateType)->TrainingAndDevelopment:
        try:
            return self.training_dev_repo.update(training_development_object=training_development_object, data=payload)
        except Exception as e:
            raise TrainingAndDevelopmentServiceErr(f"Failed to update training and development with error: {e}")

    def get_by_appraisal_id_use_case(self, appraisal_id: int)->List[TrainingAndDevelopment]:
        try:
           return self.training_dev_repo.get_by_appraisal_id(appraisal_id=appraisal_id)
        except Exception as e:
            raise TrainingAndDevelopmentServiceErr(f"Failed to retrieve all training and development by appraisal id with error: {e}")

        
    def get_by_appraisal_id_quarter_use_case(self, appraisal_id: int, year: int, quarter: int)->TrainingAndDevelopment:
        try:
            return self.training_dev_repo.get_by_appraisal_id_quarter(appraisal_id=appraisal_id, quarter=quarter, year=year)
        except Exception as e:
            raise TrainingAndDevelopmentServiceErr(f"Failed to retrieve training and development by appraisal id and quarter with error: {e}")

        
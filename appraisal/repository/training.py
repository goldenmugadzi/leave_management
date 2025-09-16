from typing import List
from django.db.models.query import QuerySet
from django.db import transaction

from ..models import TrainingAndDevelopment, Appraisal, Competency, InterventionStrategy, JobCompetency
from ..helpers.types.training import TrainingAndDevelopmentCreateUpdateType
from ..models.helpers import YearQuarter
from .departmental_workplan import JobCompetencyRepository
class TrainingAndDevelopmentRepository:
    
    def create(self, appraisal_object: Appraisal, quarter_obj: YearQuarter)->TrainingAndDevelopment:
        try:
            return TrainingAndDevelopment.objects.create(appraisal=appraisal_object, quarter=quarter_obj)
        except Exception as e:
            raise Exception(f"create TrainingAndDevelopment Repo failed with error: {e}")

    def get_by_appraisal_id_quarter(self, appraisal_id: int, quarter_id: int)->TrainingAndDevelopment:
        try:
            qr = TrainingAndDevelopment.objects.filter(appraisal__id=appraisal_id, quarter__id=quarter_id)
            
            return qr.first()
        except Exception as e:
            raise Exception(f"Get TrainingAndDevelopment by appraisal id: {appraisal_id} and quarter id: {quarter_id} Repo failed with error: {e}")
    
    def get_by_appraisal_id(self, appraisal_id: int)->TrainingAndDevelopment:
        try:
            qr = TrainingAndDevelopment.objects.filter(appraisal__id=appraisal_id).select_related('appraisal')
            
            if not qr.exists():
                return None
            return qr.first()
        except Exception as e:
            raise Exception(f"Get TrainingAndDevelopment by get_by_appraisal_id repo, appraisal id: {appraisal_id}, failed with error: {e}")
    
    def fetch_by_appraisal_id(self, appraisal_id: int)->QuerySet[TrainingAndDevelopment]:
        try:
            return TrainingAndDevelopment.objects.filter(appraisal__id=appraisal_id).select_related('appraisal')
        except Exception as e:
            raise Exception(f"Get TrainingAndDevelopment by fetch_by_appraisal_id repo, appraisal id: {appraisal_id}, failed with error: {e}")

    @transaction.atomic
    def update(self, training_development_object: TrainingAndDevelopment, data: TrainingAndDevelopmentCreateUpdateType) -> TrainingAndDevelopment:
        try:
            # Update Many-to-Many fields
            if data.existence_competencies is not None:
                training_development_object.existence_competencies.set([
                    JobCompetency.objects.get(pk=rc.id)
                    for rc in data.existence_competencies
                ])
            
            if data.intervention_strategies is not None:
                training_development_object.intervention_strategies.set([
                    InterventionStrategy.objects.get_or_create(
                        description=is_.description,
                        category=is_.category
                    )[0] for is_ in data.intervention_strategies
                ])

            # Update regular fields
            training_development_object.action_recommended = (
                data.action_recommended or training_development_object.action_recommended
            )
            training_development_object.action_taken = (
                data.action_taken or training_development_object.action_taken
            )

            # Save changes
            training_development_object.save()

            return training_development_object
        except Exception as e:
            raise Exception(f"Update TrainingAndDevelopment Repo failed with error: {e}")

    def fetch_competency_gaps(self, training_dev_obj: TrainingAndDevelopment)->List[JobCompetency]:
        try:
            designation_id = training_dev_obj.appraisal.user.designation.id
            year = training_dev_obj.quarter.year
            
            job_competency_repo = JobCompetencyRepository()
            job_competency_qr = job_competency_repo.fetch_by_designation_id_year(designation_id=designation_id, year=year)
            existing_competency_qr = training_dev_obj.existence_competencies.all()
            
            # Use set difference: job competencies not in existing competencies
            existing_ids = set(existing_competency_qr.values_list("id", flat=True))
            competency_gap = [jc for jc in job_competency_qr if jc.id not in existing_ids]
            
            return competency_gap
        except Exception as e:
            raise Exception(f"Get TrainingAndDevelopment fetch_competency_gaps with training and dev pk: {training_dev_obj.id}, failed with error: {e}")

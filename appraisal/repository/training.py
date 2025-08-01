from typing import List
from django.db.models.query import QuerySet
from django.db import transaction
from ..models import TrainingAndDevelopment, Appraisal, Competency, InterventionStrategy
from ..helpers.types.training import TrainingAndDevelopmentCreateUpdateType
from ..models.helpers import YearQuarter

class TrainingAndDevelopmentRepository:
    
    def create(self, appraisal_object: Appraisal, quarter_obj: YearQuarter)->TrainingAndDevelopment:
        try:
            return TrainingAndDevelopment.objects.create(appraisal=appraisal_object, quarter=quarter_obj)
        except Exception as e:
            raise Exception(f"create TrainingAndDevelopment Repo failed with error: {e}")

    def get_by_appraisal_id_quarter(self, appraisal_id: int, year: int, quarter: int)->TrainingAndDevelopment:
        try:
            return TrainingAndDevelopment.objects.get(appraisal__id=appraisal_id, quarter__year=year, quarter__quarter=quarter)
        except Exception as e:
            raise Exception(f"Get TrainingAndDevelopment by appraisal id and quarter Repo failed with error: {e}")
    
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
            if data.required_competencies is not None:
                training_development_object.required_competencies.set([
                    Competency.objects.get_or_create(name=rc.name)[0] for rc in data.required_competencies
                ])
            
            if data.competency_gaps is not None:
                training_development_object.competency_gaps.set([
                    Competency.objects.get_or_create(name=cg.name)[0] for cg in data.competency_gaps
                ])
            
            if data.intervention_strategies is not None:
                training_development_object.intervention_strategies.set([
                    InterventionStrategy.objects.get_or_create(
                        description=is_.description, category=is_.category
                    )[0] for is_ in data.intervention_strategies
                ])

            # Update regular fields
            training_development_object.action_recommended = data.action_recommended or training_development_object.action_recommended
            training_development_object.action_taken = data.action_taken or training_development_object.action_taken

            # Save changes
            training_development_object.save()

            return training_development_object
        except Exception as e:
            raise Exception(f"Update TrainingAndDevelopment Repo failed with error: {e}")

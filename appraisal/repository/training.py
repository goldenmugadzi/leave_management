from django.db import transaction
from ..models import TrainingAndDevelopment, Appraisal
from ..helpers.types.training import TrainingAndDevelopmentCreateUpdateType

class TrainingAndDevelopmentRepository:
    
    def create(self, appraisal_object: Appraisal, quarter: int)->TrainingAndDevelopment:
        try:
            return TrainingAndDevelopment.objects.create(appraisal=appraisal_object, quarter=quarter)
        except Exception as e:
            raise Exception(f"create TrainingAndDevelopment Repo failed with error: {e}")

    def get_by_appraisal_id_quarter(self, appraisal_id: int, quarter: int)->Appraisal:
        try:
            return TrainingAndDevelopment.objects.get(appraisal__id=appraisal_id, quarter=quarter)
        except Exception as e:
            raise Exception(f"Get TrainingAndDevelopment by appraisal id and quarter Repo failed with error: {e}")

    @transaction.atomic
    def update(self, training_development_object: TrainingAndDevelopment, data: TrainingAndDevelopmentCreateUpdateType) -> TrainingAndDevelopment:
        try:
            # Update Many-to-Many fields
            if data.required_competencies is not None:
                for required_competency in data.required_competencies: 
                    training_development_object.required_competencies.add(required_competency)
            
            if data.competency_gaps is not None:
                for competency_gap in data.competency_gaps: 
                    training_development_object.competency_gaps.add(competency_gap)

            if data.intervention_strategies is not None:
                for intervention_strategy in data.intervention_strategies: 
                    training_development_object.intervention_strategies.add(intervention_strategy)

            # Update regular fields
            if data.action_recommended is not None:
                training_development_object.action_recommended = data.action_recommended
            if data.action_taken is not None:
                training_development_object.action_taken = data.action_taken

            # Save changes
            training_development_object.save()

            return training_development_object
        except Exception as e:
            raise Exception(f"Update TrainingAndDevelopment Repo failed with error: {e}")

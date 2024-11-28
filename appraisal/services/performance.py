from typing import Dict, Any
from dataclasses import dataclass
from ..repository.performance import PerformanceReviewRepository
from ..models import Appraisal, PerformanceProgressReview
from ..helpers.types import PerformanceReviewType, StrengthAndWeaknessTypes
from ..helpers.setters import map_performance_strengths

class PerformanceReviewServiceError(Exception):
    pass


@dataclass
class PerformanceReviewService:
    performance_repo: PerformanceReviewRepository
    
    def create_use_case(self, appraisal_object: Appraisal, data: PerformanceReviewType)->PerformanceProgressReview:
        try:
            performance_object = self.performance_repo.create(appraisal_object=appraisal_object, data=data)
            return performance_object
        except Exception as e:
            raise PerformanceReviewServiceError(f"Failed to create performance review with error: {e}")
        
    
    
    def add_strengths_use_case(self, performance_review_object: PerformanceProgressReview, strengths: StrengthAndWeaknessTypes):
        try:
            strengths_objects = map_performance_strengths(strengths=strengths)
            self.performance_repo.add_strengths(performance_review_object=performance_review_object, strengths=strengths_objects)
        except Exception as e:
            raise PerformanceReviewServiceError(f"Failed to add performance strengths with error: {e}")

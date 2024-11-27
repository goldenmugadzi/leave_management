from typing import Dict, Any
from dataclasses import dataclass
from ..repository.performance import PerformanceReviewRepository
from ..models import Appraisal, PerformanceProgressReview
from ..helpers.types import PerformanceReviewType

@dataclass
class PerformanceReviewService:
    performance_repo: PerformanceReviewRepository
    
    def create_use_case(self, appraisal_object: Appraisal, data: PerformanceReviewType)->PerformanceProgressReview:
        performance_object = self.performance_repo.create(appraisal_object=appraisal_object, data=data)
        return performance_object
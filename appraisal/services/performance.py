from typing import List
from dataclasses import dataclass
from ..repository.performance import PerformanceReviewRepository
from ..models import Appraisal, PerformanceProgressReview
from ..helpers.types import PerformanceReviewType, StrengthAndWeaknessTypes
from ..helpers.setters import map_performance_strengths, map_performance_weaknesses

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



    def add_strengths_use_case(self, performance_review_object: PerformanceProgressReview, strengths: List[StrengthAndWeaknessTypes]):
        try:
            strengths_objects = map_performance_strengths(strengths=strengths)
            self.performance_repo.add_strengths(performance_review_object=performance_review_object, strengths=strengths_objects)
        except Exception as e:
            raise PerformanceReviewServiceError(f"Failed to add performance strengths with error: {e}")

    def add_weakness_use_case(self, performance_review_object: PerformanceProgressReview, weaknesses: List[StrengthAndWeaknessTypes]):
        try:
            weaknesses_objects = map_performance_weaknesses(weaknesses=weaknesses)
            self.performance_repo.add_weaknesses(performance_review_object=performance_review_object, weaknesses=weaknesses_objects)
        except Exception as e:
            raise PerformanceReviewServiceError(f"Failed to add performance weaknesses with error: {e}")

    def get_all_performance_use_case(self)->List[PerformanceProgressReview]:
        try:
           return self.performance_repo.get_all_performance()
        except Exception as e:
            raise PerformanceReviewServiceError(f"Failed to retrieve all performance with error: {e}")

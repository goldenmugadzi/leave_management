from typing import List
from dataclasses import dataclass
from ..repository.performance import PerformanceReviewRepository
from ..models import Appraisal, PerformanceProgressReview, PerformanceProgressStrength, PerformanceProgressWeakness
from ..helpers.types import PerformanceReviewType
from ..models.helpers import YearQuarter

class PerformanceReviewServiceError(Exception):
    pass


@dataclass
class PerformanceReviewService:
    performance_repo: PerformanceReviewRepository

    def create_use_case(self, appraisal_object: Appraisal, year_quarter_object: YearQuarter)->PerformanceProgressReview:
        try:
            performance_object = self.performance_repo.create(appraisal_object=appraisal_object, year_quarter_object=year_quarter_object)
            return performance_object
        except Exception as e:
            raise PerformanceReviewServiceError(f"Failed to create performance review with error: {e}")



    def add_strengths_use_case(self, performance_review_object: PerformanceProgressReview, strengths: List[PerformanceProgressStrength]):
        try:
            self.performance_repo.add_strengths(performance_review_object=performance_review_object, strengths=strengths)
        except Exception as e:
            raise PerformanceReviewServiceError(f"Failed to add performance strengths with error: {e}")

    def add_weakness_use_case(self, performance_review_object: PerformanceProgressReview, weaknesses: List[PerformanceProgressWeakness]):
        try:
            self.performance_repo.add_weaknesses(performance_review_object=performance_review_object, weaknesses=weaknesses)
        except Exception as e:
            raise PerformanceReviewServiceError(f"Failed to add performance weaknesses with error: {e}")

    def get_all_performance_use_case(self)->List[PerformanceProgressReview]:
        try:
           return self.performance_repo.get_all_performance()
        except Exception as e:
            raise PerformanceReviewServiceError(f"Failed to retrieve all performance with error: {e}")

    def get_performances_by_appraisal_id_use_case(self, appraisal_id: int)->List[PerformanceProgressReview]:
        try:
           return self.performance_repo.get_performance_by_appraisal_id(appraisal_id=appraisal_id)
        except Exception as e:
            raise PerformanceReviewServiceError(f"Failed to retrieve performance by appraisal with error: {e}")

    def get_performances_by_appraisal_id_quarter_use_case(self, appraisal_id: int, year: int, quarter: int)->PerformanceProgressReview|None:
        try:
           return self.performance_repo.get_performance_by_appraisal_id_quarter(appraisal_id=appraisal_id, year=year, quarter=quarter)
        except Exception as e:
            raise PerformanceReviewServiceError(f"Failed to retrieve performance by appraisal with error: {e}")

    def get_performance_by_id_use_case(self, pk: int)->PerformanceProgressReview:
        try:
           return self.performance_repo.get_performance_by_id(pk=pk)
        except Exception as e:
            raise PerformanceReviewServiceError(f"Failed to retrieve performance by id with error: {e}")

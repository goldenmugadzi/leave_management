from typing import List
from ..models import Appraisal, PerformanceProgressReview, PerformanceProgressStrength, PerformanceProgressWeakness
from ..models.helpers import YearQuarter

class PerformanceReviewRepository:
    def create(self, appraisal_object: Appraisal, year_quarter_object: YearQuarter)->PerformanceProgressReview:
        try:
            return PerformanceProgressReview.objects.get_or_create(appraisal=appraisal_object, quarter=year_quarter_object)
        except Exception as e:
            raise Exception(f"PerformanceReview create repo failed with error: {e}")
        
    def add_strengths(self, performance_review_object: PerformanceProgressReview, strengths: List[PerformanceProgressStrength]):
        try:
            performance_review_object.strengths.add(*strengths)
            return None
        except Exception as e:
            raise Exception(f"PerformanceReview add strengths repo failed with error: {e}")
    
    def add_weaknesses(self, performance_review_object: PerformanceProgressReview, weaknesses: List[PerformanceProgressWeakness]):
        try:
            performance_review_object.areas_of_weaknesses.add(*weaknesses)
            return None
        except Exception as e:
            raise Exception(f"PerformanceReview add weaknesses repo failed with error: {e}")

    def get_strength_by_name(self, name: str)->PerformanceProgressStrength:
        try:
            return PerformanceProgressStrength.objects.get(name=name)
        except Exception as e:
            raise ValueError(f"retrieve strength object failed with error: {e}")
    
    def get_weakness_by_name(self, name: str)->PerformanceProgressWeakness:
        try:
            return PerformanceProgressWeakness.objects.get(name=name)
        except Exception as e:
            raise ValueError(f"retrieve weakness object failed with error: {e}")
        
    def get_all_performance(self)->List[PerformanceProgressReview]:
        try:
            return PerformanceProgressReview.objects.all().order_by('-created_date', '-updated')
        except Exception as e:
            raise ValueError(f"retrieving all performance objects failed with error: {e}")
    
    def get_performance_by_appraisal_id(self, appraisal_id: int)->List[PerformanceProgressReview]:
        try:
            return PerformanceProgressReview.objects.filter(appraisal__id=appraisal_id)
        except Exception as e:
            raise ValueError(f"retrieving performance objects by appraisal failed with error: {e}")
    
    
    def get_performance_by_appraisal_id_quarter(self, appraisal_id: int, year: int, quarter: int)->PerformanceProgressReview:
        try:
            object = PerformanceProgressReview.objects.filter(appraisal__id=appraisal_id, quarter__year=year, quarter__quarter=quarter)
            if len(object) == 0:
                return None
            return object.first()
        except Exception as e:
            raise ValueError(f"retrieving performance objects by appraisal failed with error: {e}")
    
    def get_performance_by_id(self, pk: int)->PerformanceProgressReview:
        try:
            return PerformanceProgressReview.objects.get(id=pk)
        except Exception as e:
            raise ValueError(f"retrieving performance object by pk failed with error: {e}")

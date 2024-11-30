from typing import List
from ..models import Appraisal, PerformanceProgressReview, PerformanceProgressStrength, PerformanceProgressWeakness
from ..helpers.types import PerformanceReviewType

class PerformanceReviewRepository:
    def create(self, appraisal_object: Appraisal, data: PerformanceReviewType)->PerformanceProgressReview:
        try:
            return PerformanceProgressReview.objects.get_or_create(appraisal=appraisal_object, quarter=data.quarter)
        except Exception as e:
            raise Exception(f"PerformanceReview create repo failed with error: {e}")
        
    def add_strengths(self, performance_review_object: PerformanceProgressReview, strengths: List[PerformanceProgressStrength]):
        try:
            if not isinstance(list, strengths):
                raise ValueError("PerformanceReview add strengths a list of strengths")
            
            if len(strengths) == 0:
                raise Exception("EPerformanceReview add strengths failed with error: empty strengths list")
            
            performance_review_object.strength.add(*strengths)
            return None
        except Exception as e:
            raise Exception(f"PerformanceReview add strengths repo failed with error: {e}")
    
    def add_weaknesses(self, performance_review_object: PerformanceProgressReview, weaknesses: List[PerformanceProgressWeakness]):
        try:
            if not isinstance(list, weaknesses):
                raise ValueError("PerformanceReview add weaknesses a list of weaknesses")
            
            if len(weaknesses) == 0:
                raise Exception("EPerformanceReview add weaknesses failed with error: empty weaknesses list")
            
            performance_review_object.areas_of_weakness.add(*weaknesses)
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

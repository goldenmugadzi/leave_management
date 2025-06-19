from typing import Dict
from ...repository.kra import TargetScoreRepository


class ActivityScoreHandler:
    def __get_scores_objects_current_quarter(self, appraisal_id: int, quarter: int, year: int):        
        activity_score_repo = TargetScoreRepository()
        activity_score_qr = activity_score_repo.fetch_by_appraisal_id(appraisal_id=appraisal_id)
        return activity_score_qr.filter(performance_dimension__activity__appraisal_kra__quarter__year=year, 
                                        performance_dimension__activity__appraisal_kra__quarter__quarter=quarter)

    
    def get_activity_scores_quarter_scored(self, appraisal_id: int, quarter: int, year: int)->Dict[str, bool]:
        data = {"activity_scores_quarter_scored": False}
        
        scores_current_quarter_qr = self.__get_scores_objects_current_quarter(appraisal_id=appraisal_id, year=year, quarter=quarter)
        if scores_current_quarter_qr.exists():
            unscored_current_quarter_activity_scores_qr = scores_current_quarter_qr.filter(is_scored=False)
            
            if not unscored_current_quarter_activity_scores_qr.exists():
                data["activity_scores_quarter_scored"] = True
        return data
from typing import List, Tuple
from datetime import date
from dateutil.relativedelta import relativedelta
from ..types.final_results import FinalRatingType
from ...templatetags.kra_calculations import get_department_objectives_total_year_quarter_weighted_score
from ...repository.kra import YearQuarterRepository


def get_all_quarter_ratings_per_appraiser(year: int, appraisal_id: int)->Tuple[List[FinalRatingType], float]:
    quarters = []
    start_date = date(year, 1, 1)
    quarters_name = [
        (0, "First Quarter"),
        (1, "Second Quarter"),
        (2, "Third Quarter"),
        (3, "Fourth Quarter"),
    ]

    final_score = 0
    repo = YearQuarterRepository()
    for quarter in quarters_name:
        quarter_start_date = start_date + relativedelta(months=3*quarter[0])
        quarter_end_date = quarter_start_date + relativedelta(months=3) - relativedelta(days=1)
        quarter_obj = repo.get_by_year_quarter(year=year, quarter=int(quarter[0]+1))
        total_score = get_department_objectives_total_year_quarter_weighted_score(
            year_quarter_id=quarter_obj.id,
            appraisal_id=appraisal_id
        )
        final_rating_type = FinalRatingType(name=quarter[1], start_date=quarter_start_date, end_date=quarter_end_date, total_score=total_score)
        
        final_score = final_score + total_score
        quarters.append(final_rating_type)
        
    return quarters, final_score
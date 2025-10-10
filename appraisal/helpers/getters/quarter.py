from typing import List, Tuple
from datetime import date
from dateutil.relativedelta import relativedelta
from ..types.final_results import FinalRatingType
from ...templatetags.kra_calculations import get_department_objectives_total_year_quarter_weighted_score
from ...repository.kra import YearQuarterRepository, AppraisalOutPutPerformanceDimensionScoreRepository
from ...helpers.types.appraisal import FinalScoreType


def get_all_quarter_ratings_per_appraiser(year: int, appraisal_id: int)->FinalScoreType:
    """
        Retrieve and calculate quarterly performance ratings for a given appraisal within a specified year.

        This function calculates the weighted performance scores for each of the four quarters in a given year, 
        based on the department objectives and appraisal performance dimension scores. It returns a list of 
        quarterly ratings along with an overall final score.

        The final score is adjusted by deducting unscored quarters and dividing by the number of scored quarters. 
        If no quarters are scored, the denominator is set to 1 to avoid division by zero.

        Args:
            year (int): The year for which to retrieve quarterly ratings.
            appraisal_id (int): The appraisal identifier used to fetch scores.

        Returns:
            FinalScoreType:
                - A list of `FinalRatingType` objects, each representing the score and metadata for a quarter.
                - A float representing the overall final score across the year.
        
        Notes:
            - Quarters are defined as:
                1. First Quarter: January 1 – March 31
                2. Second Quarter: April 1 – June 30
                3. Third Quarter: July 1 – September 30
                4. Fourth Quarter: October 1 – December 31
            - If all quarters are unscored, the divisor defaults to 1 to avoid errors.
    """
    
    quarters = []
    start_date = date(year, 1, 1)
    quarters_name = [
        (0, "First Quarter"),
        (1, "Second Quarter"),
        (2, "Third Quarter"),
        (3, "Fourth Quarter"),
    ]

    final_score = 0
    total_scored_quarters = 0
    total_unscored_quarters = 0
    
    repo = YearQuarterRepository()
    scores_repo = AppraisalOutPutPerformanceDimensionScoreRepository()
    
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
        
        dimension_score_qr = scores_repo.fetch_by_appraisal_id_year_quarter_id(
            year_quarter_id=quarter_obj.id,
            appraisal_id=appraisal_id
        ) 
        
        
        unscored_dimension_score_qr = dimension_score_qr.filter(is_scored=False)

        if not unscored_dimension_score_qr.exists():
            total_scored_quarters = total_scored_quarters + 1
        else:
            total_unscored_quarters = total_unscored_quarters + 1
        quarters.append(final_rating_type)
    
    if total_scored_quarters == 0:
        total_scored_quarters = 1
    
    final_score = (final_score - total_unscored_quarters)/total_scored_quarters
    
    return FinalScoreType(
        final_score=final_score,
        rating=quarters
    )
from decouple import config
from datetime import datetime, date

class AppraisalDatesRulesHandler:
    def __init__(self):
        env_var = config('APPRAISAL_EXTENDED_YEAR_DATE', cast=str)
        self.extended_date_object = datetime.strptime(env_var, "%y-%m-%d")
        self.current_date = datetime.now()
    
    def is_within_extended_year(self):
        if self.current_date <= self.extended_date_object:
            return True
        return False
    
    def get_prev_year_end_date(self):
        last_yr_yr = self.current_date.year-1
        last_yr_end_date = date(last_yr_yr, 12, 31)
        return last_yr_end_date
    
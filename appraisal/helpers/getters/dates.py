from dataclasses import dataclass
from typing import Tuple
from datetime import date
from dateutil.relativedelta import relativedelta
from ..types.quarters import CurrentQuartersType
from ..rules import AppraisalDatesRulesHandler

def get_assessment_period(date_object):
    year = date_object.year    
    return f"From: 01/01/{year} To: 31/12/{year}"

@dataclass
class CurrentQuarterDate:
    year: int
    
    def get_year_first_date(self):
        return date(year=self.year, month=1, day=1)
    
    def get_end_date(self, start_date: date)->date:
        next_2_months = start_date + relativedelta(months=3)
        end_date = next_2_months - relativedelta(days=1)
        return end_date
    
    def first_q_start_end_dates(self)->Tuple[date, date]:
        start_date = self.get_year_first_date()
        end_date = self.get_end_date(start_date=start_date)
        return start_date, end_date
    
    def second_q_start_end_dates(self)->Tuple[date, date]:
        _, first_q_end_date = self.first_q_start_end_dates()
        start_date = first_q_end_date + relativedelta(days=1)
        end_date = self.get_end_date(start_date=start_date)
        return start_date, end_date

    def third_q_start_end_dates(self)->Tuple[date, date]:
        _, second_q_end_date = self.second_q_start_end_dates()
        start_date = second_q_end_date + relativedelta(days=1)
        end_date = self.get_end_date(start_date=start_date)
        return start_date, end_date
    
    def fourth_q_start_end_dates(self)->Tuple[date, date]:
        _, third_q_end_date = self.third_q_start_end_dates()
        start_date = third_q_end_date + relativedelta(days=1)
        end_date = self.get_end_date(start_date=start_date)
        return start_date, end_date
    
    def is_within_range(self, first_date: date, end_date: date)->bool:
        current_date = date.today()
        if first_date <= current_date <= end_date:
            return True
        return False
    
    def get_current_quarter(self)->CurrentQuartersType:
        first_q_start_date, first_q_end_date = self.first_q_start_end_dates()
        second_q_start_date, second_q_end_date = self.second_q_start_end_dates()
        third_q_start_date, third_q_end_date = self.third_q_start_end_dates()
        fourth_q_start_date, fourth_q_end_date = self.fourth_q_start_end_dates()
        
        date_rules_handler = AppraisalDatesRulesHandler()
        if date_rules_handler.is_within_extended_year():
            return CurrentQuartersType(
                is_within_first_quarter=False,
                is_within_second_quarter=False,
                is_within_third_quarter=False,
                is_within_fourth_quarter=True
            )
        
        return CurrentQuartersType(
            is_within_first_quarter=self.is_within_range(first_date=first_q_start_date, end_date=first_q_end_date),
            is_within_second_quarter=self.is_within_range(first_date=second_q_start_date, end_date=second_q_end_date),
            is_within_third_quarter=self.is_within_range(first_date=third_q_start_date, end_date=third_q_end_date),
            is_within_fourth_quarter=self.is_within_range(first_date=fourth_q_start_date, end_date=fourth_q_end_date)
        )
        
    def get_quarter_for_date(self, target_date: date) -> int:
        """Return the quarter number (1–4) for the given date."""
        if 1 <= target_date.month <= 3:
            return 1
        elif 4 <= target_date.month <= 6:
            return 2
        elif 7 <= target_date.month <= 9:
            return 3
        elif 10 <= target_date.month <= 12:
            return 4
        else:
            raise ValueError("Invalid month in date")
        
    
    
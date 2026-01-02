from django import template
from datetime import date
from dateutil.relativedelta import relativedelta
from ..helpers.types.approval import ApprovalStageChoices
from ..helpers.rules import AppraisalDatesRulesHandler

register = template.Library()

@register.filter
def quarter_name(quarter):
    quarters = {
        1: "First Quarter",
        2: "Second Quarter",
        3: "Third Quarter",
        4: "Fourth Quarter"
    }
    return quarters.get(int(quarter), "")

@register.filter
def get_current_quarter(value):
    today = date.today()
    current_yr = today.year

    start_date = date(current_yr, 1, 1)
    
    date_handler = AppraisalDatesRulesHandler()
    if date_handler.is_within_extended_year():
        return ApprovalStageChoices.Fourth_Quarter.value

    for index, quarter in enumerate(ApprovalStageChoices):
        quarter_start_date = start_date + relativedelta(months=3 * index)
        quarter_end_date = quarter_start_date + relativedelta(months=3) - relativedelta(days=1)

        # Special check for 4th quarter already completed
        if quarter == ApprovalStageChoices.Fourth_Quarter and today > quarter_end_date:
            return "Completed"

        if quarter_start_date <= today <= quarter_end_date:
            return quarter.value  # return e.g. "First Quarter"

    return None
    
from django import template

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

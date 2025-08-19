

def percentage_validation(percentage_value: int, field_name: str):

    if percentage_value < 0 or percentage_value > 100:
        raise ValueError(f"{field_name} must be a percentage between 0 and 100")
    return percentage_value
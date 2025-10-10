

def percentage_validation(percentage_value: int, field_name: str):

    if percentage_value < 0:
        raise ValueError(f"{field_name} must be a percentage greater than 0")
    return percentage_value
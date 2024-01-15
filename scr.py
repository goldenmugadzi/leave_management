import csv
import random
import string
from datetime import datetime, timedelta

def get_random_date(start_date, end_date):
    """
    Returns a random date between start_date and end_date (inclusive).
    """
    days_between = (end_date - start_date).days
    random_days = random.randint(0, days_between)
    random_date = start_date + timedelta(days=random_days)
    return random_date.strftime("%Y-%m-%d")

# Sample data arrays
depots = [
    "Mabelreign Depot",
    "Borrowdale Depot",
    "Glen View Depot",
    "Kuwadzana Depot",
    "Mabvuku Depot",
    "Ruwa Depot",
    "Southerton Depot",
    "Warren Park Depot",
    "Waterfalls Depot",
    "CBD Depot",
    "Makoni Depot",
    "Zengeza Depot",
    "Seke"
]

districts = [
    "Chitungwiza District",
    "North District",
    "South District",
    "East District"
]

regions = [
    "Harare",
    "East",
    "South",
    "West"
]

# Generate random data points
dataPoints = []
numDataPoints = min(100, random.randint(1, 101))  # Generate up to 100 data points

for i in range(numDataPoints):
    clientFullname = "Client " + str(i + 1)
    depot = random.choice(depots)
    district = random.choice(districts)
    region = random.choice(regions)
    
    start_date = datetime(2023, 12, 1)
    end_date = datetime(2024, 1, 9)
    random_date = get_random_date(start_date, end_date)
    createdAt = random_date
    
    amount = "$" + str(random.randint(1, 100))

    dataPoint = {
        "client_fullname": clientFullname,
        "depot": depot,
        "district": district,
        "region": region,
        "created_at": createdAt,
        "amount": amount
    }

    dataPoints.append(dataPoint)

# Write data points to a CSV file
filename = "td_data.csv"
fieldnames = ["client_fullname", "depot", "district", "region", "created_at", "amount"]

with open(filename, "w", newline="") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(dataPoints)

print("CSV file generated:", filename)
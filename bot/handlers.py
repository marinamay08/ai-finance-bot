import re
import csv
from datetime import datetime

def parse_expense(text: str):
    match = re.match(r"(\d+)\s+(.+)", text)
    if not match:
        return None
    amount = int(match.group(1))
    category = match.group(2).strip()
    return amount, category

def save_expence_to_csv(amount, category, username="User"):
    with open("data/expences.csv", "a") as f:
        writer = csv.writer(f)
        writer.writerow([datetime.now().date(), amount, category, username])

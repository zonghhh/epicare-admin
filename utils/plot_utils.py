import csv
from datetime import datetime, timedelta
from collections import defaultdict

def get_pageview_data(log_file_path):
    # plotting code

    today = datetime.now().date()
    yesterday = today - timedelta(days=1)

    # defaultdict(int) automatically creates default values for missing keys
    counts = {
        'Admin': defaultdict(int),
        'Caretaker': defaultdict(int),
        'PWID': defaultdict(int)
    }

    with open(log_file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f) # read the csv
        for row in reader:
            ts = datetime.fromisoformat(row['timestamp']) # get timestamp
            user_type = row['user_type'].strip()

            if ts.date() == yesterday and user_type in counts:
                hour = ts.hour
                counts[user_type][hour] += 1
    
    for user_type in counts:
        for h in range(24):
            if h not in counts[user_type]:
                counts[user_type][h] = 0 # create entry for every hour to fill in missing hours

    # prep data for Chart.js
    hours = list(range(24))
    return {
        'hours': hours,
        'Admin': [counts["Admin"][h] for h in hours],
        'Caretaker': [counts["Caretaker"][h] for h in hours],
        'PWID': [counts["PWID"][h] for h in hours]
    }

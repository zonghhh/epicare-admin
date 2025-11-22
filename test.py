import shelve
from datetime import datetime
from accounts.PWID import PWID
from accounts.Caretaker import Caretaker

ADMIN_SHELVE_NAME = 'admin_accounts.db'  # adjust to your actual file name

with shelve.open(ADMIN_SHELVE_NAME, writeback=True) as db:
    # Optional: Clear existing data
    db.clear()

    # Add multiple PWIDs
    for i in range(1, 4):  # creates 3 PWIDs
        username = f"pwid{i}"
        user = PWID(
            username=username,
            email=f"{username}@example.com",
            password="password123",
            job='Teacher'
        )
        # Set creation date to a fixed past date for testing
        user.creation_date = datetime(2024, 1, 1)
        user.page_views = 5 * i  # example page views count
        db[username] = user

    # Add multiple Caretakers
    for i in range(1, 3):  # creates 2 Caretakers
        username = f"caretaker{i}"
        user = Caretaker(
            username=username,
            email=f"{username}@example.com",
            password="password123",
            job="Nurse"
        )
        user.creation_date = datetime(2024, 6, 1)
        user.page_views = 10 * i
        db[username] = user

    print(f"Created {len(db)} test users")

with shelve.open(ADMIN_SHELVE_NAME) as db:
    for key, user in db.items():
        print(key, user.get_user_type(), user.creation_date, user.page_views)

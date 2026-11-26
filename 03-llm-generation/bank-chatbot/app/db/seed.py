import sqlite3
import random


FIRST_NAMES = [
    "Avery", "Bailey", "Cameron", "Dakota", "Emerson", "Finley", "Gray", "Harper", "Indigo", "Jordan",
    "Kai", "Logan", "Morgan", "Noel", "Oakley", "Parker", "Quinn", "Riley", "Sage", "Taylor",
    "Uma", "Valentine", "Winter", "Xavier", "Yael", "Zion", "Amara", "Beckett", "Clara", "Dylan",
    "Elodie", "Felix", "Gemma", "Hugo", "Iris", "Jonah", "Keira", "Leon", "Mila", "Nico",
    "Orla", "Priya", "Rafael", "Sofia", "Theo", "Vera", "Wesley", "Yara", "Zara", "Adrian",
]
LAST_NAMES = [
    "Bennett", "Caldwell", "Delaney", "Ellis", "Fletcher", "Gallagher", "Hayes", "Ibrahim", "Jensen", "Keller",
    "Lawson", "Mercer", "Nakamura", "Olsen", "Patel", "Quincy", "Reeves", "Singh", "Turner", "Usman",
    "Vaughn", "Walsh", "Xu", "Young", "Zimmerman", "Anders", "Brooks", "Costa", "Doyle", "Evans",
    "Farouk", "Grant", "Haddad", "Ivanov", "James", "Kim", "Lopez", "Meyer", "Novak", "Owens",
    "Price", "Reyes", "Shah", "Thomas", "Ueda", "Vasquez", "White", "Yilmaz", "Zhou", "Armstrong",
]


def seed_demo_data(connection: sqlite3.Connection) -> None:
    rng = random.Random(271828)
    first_names = FIRST_NAMES.copy()
    last_names = LAST_NAMES.copy()
    rng.shuffle(first_names)
    rng.shuffle(last_names)
    generated_names = [f"{first} {last}" for first, last in zip(first_names, last_names, strict=True)]
    connection.executemany(
        "INSERT OR IGNORE INTO customers(id, name, email) VALUES (?, ?, ?)",
        [
            ("CUST-1001", "Alex Morgan", "alex@example.test"),
            ("CUST-1002", "Jamie Lee", "jamie@example.test"),
        ],
    )
    connection.executemany(
        "INSERT OR IGNORE INTO accounts VALUES (?, ?, ?, ?, ?)",
        [
            ("ACC-1001-01", "CUST-1001", "checking", "EUR", 245_075),
            ("ACC-1001-02", "CUST-1001", "savings", "EUR", 1_250_000),
            ("ACC-1002-01", "CUST-1002", "checking", "EUR", 98_450),
        ],
    )
    connection.executemany(
        "INSERT OR IGNORE INTO transactions VALUES (?, ?, ?, ?, ?, ?)",
        [
            ("TX-1001-01", "ACC-1001-01", "Grocery Market", -7_250, "EUR", "2026-11-20T10:30:00+00:00"),
            ("TX-1001-02", "ACC-1001-01", "Salary payment", 250_000, "EUR", "2026-11-18T08:15:00+00:00"),
            ("TX-1001-03", "ACC-1001-02", "Monthly savings transfer", 25_000, "EUR", "2026-11-17T09:00:00+00:00"),
            ("TX-1002-01", "ACC-1002-01", "Bookshop", -2_480, "EUR", "2026-11-21T14:10:00+00:00"),
        ],
    )
    connection.executemany(
        "INSERT OR IGNORE INTO loans VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            ("LN-1001-01", "CUST-1001", "personal", 800_000, 512_000, 24_500, "active"),
            ("LN-1002-01", "CUST-1002", "auto", 1_500_000, 0, 0, "paid_off"),
        ],
    )
    connection.executemany(
        "INSERT OR IGNORE INTO cards VALUES (?, ?, ?, ?, ?, ?)",
        [
            ("CARD-1001-01", "CUST-1001", "standard", 300_000, 224_500, "active"),
            ("CARD-1002-01", "CUST-1002", "none", 0, 0, "not_issued"),
        ],
    )
    connection.executemany(
        "INSERT OR IGNORE INTO recurring_payments VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [
            ("RP-1001-01", "CUST-1001", "Northside Internet", 4_990, "EUR", "monthly", "2026-12-01", "active"),
            ("RP-1001-02", "CUST-1001", "City Gym", 3_500, "EUR", "monthly", "2026-12-05", "active"),
            ("RP-1002-01", "CUST-1002", "StreamCo", 1_299, "EUR", "monthly", "2026-11-28", "active"),
        ],
    )
    connection.executemany(
        "INSERT OR IGNORE INTO faqs VALUES (?, ?, ?, ?)",
        [
            ("FAQ-001", "How do I report a lost card?", "Freeze the card in your banking app, then call the 24/7 card support number printed on the bank website.", "cards"),
            ("FAQ-002", "When do bank transfers arrive?", "Standard transfers usually arrive within one business day. Timing depends on the payment rail and receiving bank.", "payments"),
            ("FAQ-003", "How can I update my contact details?", "Sign in to online banking and open Profile and contact details. Some changes require identity verification.", "account"),
            ("FAQ-004", "What should I do if I suspect fraud?", "Lock affected cards if possible and contact the bank using the phone number on its official website.", "security"),
        ],
    )
    # Fifty additional deterministic profiles make profile switching and
    # correctness-under-concurrency checks easy to reproduce.
    for number in range(1003, 1053):
        customer_id = f"CUST-{number}"
        suffix = number - 1000
        connection.execute(
            "INSERT INTO customers(id, name, email) VALUES (?, ?, ?) "
            "ON CONFLICT(id) DO UPDATE SET name = excluded.name, email = excluded.email",
            (customer_id, generated_names[suffix - 3], f"customer{number}@example.test"),
        )
        account_id = f"ACC-{number}-01"
        connection.execute(
            "INSERT OR IGNORE INTO accounts VALUES (?, ?, ?, ?, ?)",
            (account_id, customer_id, "checking", "EUR", 50_000 + (suffix * 1_337)),
        )
        connection.execute(
            "INSERT OR IGNORE INTO transactions VALUES (?, ?, ?, ?, ?, ?)",
            (f"TX-{number}-01", account_id, "Demo deposit", 50_000, "EUR", "2026-11-20T10:30:00+00:00"),
        )
        # Alternate records so all tools can be exercised across the cohort.
        if suffix % 2 == 0:
            connection.execute(
                "INSERT OR IGNORE INTO loans VALUES (?, ?, ?, ?, ?, ?, ?)",
                (f"LN-{number}-01", customer_id, "personal", 400_000, 250_000, 12_500, "active"),
            )
        connection.execute(
            "INSERT OR IGNORE INTO cards VALUES (?, ?, ?, ?, ?, ?)",
            (f"CARD-{number}-01", customer_id, "standard", 200_000 + (suffix * 100), 150_000, "active"),
        )
        if suffix % 3 == 0:
            connection.execute(
                "INSERT OR IGNORE INTO recurring_payments VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (f"RP-{number}-01", customer_id, "Demo utility", 2_500, "EUR", "monthly", "2026-12-01", "active"),
            )
    connection.commit()


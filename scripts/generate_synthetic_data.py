from __future__ import annotations

import hashlib
import json
import random
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

SEED = 20260907
random.seed(SEED)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_FILE = PROJECT_ROOT / "database" / "seeds" / "002_seed_synthetic_data.sql"

TENANT_CODE = "SLBANK01"
TENANT_NAME = "Lanka Digital Banking Ltd"

TODAY = date(2026, 9, 7)
START_DATE = date(2025, 1, 1)

NUM_CUSTOMERS = 100
NUM_ACCOUNTS = 150
NUM_ACCOUNT_TRANSACTIONS = 3000
NUM_CARDS = 150
NUM_CARD_TRANSACTIONS = 2000
NUM_LOANS = 50
NUM_LOAN_PAYMENTS = 500
NUM_BENEFICIARIES = 200
NUM_PAYMENTS = 300
NUM_COMPLAINTS = 100
NUM_TICKETS = 100
NUM_CONVERSATIONS = 200
NUM_MESSAGES = 1000
NUM_TOOL_EXECUTIONS = 250
NUM_AUDIT_LOGS = 500


# ============================================================
# SRI LANKAN SYNTHETIC DATA
# ============================================================

MALE_FIRST_NAMES = [
    "Kasun", "Nimal", "Tharindu", "Chamod", "Dinesh",
    "Ravindu", "Isuru", "Dilshan", "Chamara", "Sahan",
    "Pasindu", "Lahiru", "Gihan", "Supun", "Rukshan",
    "Akila", "Kavindu", "Sachith", "Dinuka", "Janith",
    "Malith", "Sandun", "Shehan", "Naveen", "Pramod",
]

FEMALE_FIRST_NAMES = [
    "Dilani", "Tharushi", "Hashini", "Sachini", "Nethmi",
    "Hansika", "Kavindi", "Dinithi", "Chamari", "Shenali",
    "Piumi", "Isuri", "Anuki", "Hiruni", "Amaya",
    "Sewmi", "Ayesha", "Fathima", "Nimra", "Shakira",
    "Yasmin", "Nadeesha", "Madhavi", "Sanduni", "Vihangi",
]

SINHALA_SURNAMES = [
    "Perera", "Fernando", "Silva", "Jayasinghe", "Bandara",
    "Rathnayake", "Wickramasinghe", "Gunawardena", "Senanayake",
    "Wijesinghe", "Dissanayake", "Karunaratne", "Herath",
    "Kumara", "Samarasinghe", "Rajapaksha", "Ekanayake",
]

TAMIL_NAMES = [
    "Arun Kumar", "Suresh Kumar", "Karthik Raj",
    "Aravind Kumar", "Vijay Raj", "Pradeep Kumar",
    "Naveen Raj", "Tharshan", "Yogesh",
    "Harini", "Kavitha", "Nivetha", "Janani",
    "Deepika", "Sharmila", "Meena",
]

MUSLIM_NAMES = [
    "Mohamed Rizwan", "Mohamed Azeez", "Mohamed Irfan",
    "Abdul Rahman", "Abdul Hameed", "Ahamed Fawzan",
    "Fathima Nazeera", "Fathima Rizana", "Ayesha Farook",
    "Nimra Ahamed", "Shakira Mohamed", "Safiya Rahman",
]

CITIES = [
    "Colombo",
    "Dehiwala-Mount Lavinia",
    "Sri Jayawardenepura Kotte",
    "Negombo",
    "Gampaha",
    "Kandy",
    "Nuwara Eliya",
    "Matale",
    "Galle",
    "Matara",
    "Hambantota",
    "Jaffna",
    "Vavuniya",
    "Kurunegala",
    "Puttalam",
    "Anuradhapura",
    "Polonnaruwa",
    "Ratnapura",
    "Kegalle",
    "Badulla",
    "Monaragala",
    "Batticaloa",
    "Trincomalee",
    "Ampara",
]

BANKS = [
    "Bank of Ceylon",
    "People's Bank",
    "Commercial Bank",
    "Sampath Bank",
    "Hatton National Bank",
    "Nations Trust Bank",
    "National Development Bank",
    "DFCC Bank",
    "Seylan Bank",
    "National Savings Bank",
    "Pan Asia Bank",
    "Amana Bank",
]

MERCHANTS = [
    "Keells",
    "Cargills Food City",
    "Arpico",
    "Glomark",
    "Laugfs Super",
    "Dialog",
    "SLT-Mobitel",
    "Hutch",
    "PickMe",
    "Uber",
    "CEYPETCO",
    "Lanka IOC",
    "KFC Sri Lanka",
    "Pizza Hut Sri Lanka",
    "Domino's Sri Lanka",
    "Odel",
    "Singer",
    "Abans",
    "Healthguard",
    "Asiri Pharmacy",
    "Daraz",
]

BILL_MERCHANTS = [
    "CEB",
    "LECO",
    "NWSDB",
    "Dialog",
    "SLT-Mobitel",
    "Hutch",
]

TRANSACTION_CATEGORIES = [
    "Groceries",
    "Fuel",
    "Utilities",
    "Food",
    "Transport",
    "Shopping",
    "Healthcare",
    "Telecommunications",
    "Online Shopping",
    "Entertainment",
]

ACCOUNT_TYPES = [
    "savings",
    "current",
    "salary",
    "fixed_deposit",
]

LOAN_TYPES = [
    "personal",
    "home",
    "vehicle",
    "education",
    "business",
]

ACCOUNT_TRANSACTION_TYPES = [
    "purchase",
    "cash_withdrawal",
    "deposit",
    "transfer",
    "salary",
    "bill_payment",
    "fee",
    "refund",
    "interest",
    "other",
]

INTENTS = [
    "account_balance",
    "recent_transactions",
    "payment_declined",
    "lost_card",
    "block_card",
    "refund_status",
    "loan_balance",
    "make_payment",
    "complaint",
    "cefts_transfer",
]

ENGLISH_MESSAGES = {
    "account_balance": [
        "How much is my account balance?",
        "Can you check my account balance?",
        "What is my current balance?",
        "I want to know my available balance.",
    ],
    "recent_transactions": [
        "Show my last 5 transactions.",
        "Can I see my recent transactions?",
        "What were my latest transactions?",
        "Please show my transaction history.",
    ],
    "payment_declined": [
        "Why was my payment declined?",
        "My card payment was declined.",
        "Why did my transaction fail?",
        "I tried to make a payment but it was rejected.",
    ],
    "lost_card": [
        "I lost my card.",
        "My debit card is missing.",
        "I cannot find my bank card.",
        "My card was lost.",
    ],
    "block_card": [
        "Please block my card.",
        "I need to block my debit card.",
        "Can you temporarily block my card?",
        "Block my card immediately.",
    ],
    "refund_status": [
        "Where is my refund?",
        "I am waiting for a refund.",
        "Can you check my refund status?",
        "My merchant refund has not arrived.",
    ],
    "loan_balance": [
        "What is my loan balance?",
        "How much do I still owe on my loan?",
        "Can you check my outstanding loan?",
        "Show me my remaining loan amount.",
    ],
    "make_payment": [
        "I want to make a payment.",
        "Help me make a bank payment.",
        "I need to send money.",
        "I want to transfer money to a beneficiary.",
    ],
    "complaint": [
        "I want to complain about a transaction.",
        "I need to report an incorrect transaction.",
        "I have a complaint about my account.",
        "I want to raise a banking complaint.",
    ],
    "cefts_transfer": [
        "Where is my CEFTS transfer?",
        "My CEFTS transfer is still pending.",
        "Can you check my transfer status?",
        "I sent money through CEFTS. Where is it?",
    ],
}

SINHALA_MESSAGES = {
    "account_balance": [
        "මගේ ගිණුමේ ශේෂය කොපමණද?",
        "මගේ account balance එක බලන්න පුළුවන්ද?",
    ],
    "recent_transactions": [
        "මගේ අලුත්ම transactions 5 පෙන්වන්න.",
        "මගේ recent transactions බලන්න ඕන.",
    ],
    "payment_declined": [
        "මගේ payment එක decline වුණේ ඇයි?",
        "මගේ card payment එක fail වුණා.",
    ],
    "lost_card": [
        "මගේ card එක නැතිවෙලා.",
        "මගේ debit card එක හොයාගන්න බැහැ.",
    ],
    "block_card": [
        "මගේ card එක block කරන්න.",
        "කරුණාකර මගේ card එක block කරන්න.",
    ],
    "refund_status": [
        "මගේ refund එක කොහෙද?",
        "මගේ refund එක තාම ලැබුණේ නැහැ.",
    ],
    "loan_balance": [
        "මගේ loan balance එක කොපමණද?",
        "මගේ loan එකට තව කොපමණ ගෙවන්න තියෙනවද?",
    ],
    "make_payment": [
        "මට payment එකක් කරන්න ඕන.",
        "මට සල්ලි transfer කරන්න ඕන.",
    ],
    "complaint": [
        "transaction එකක් ගැන complaint එකක් දාන්න ඕන.",
        "මගේ account එක ගැන පැමිණිල්ලක් තියෙනවා.",
    ],
    "cefts_transfer": [
        "මගේ CEFTS transfer එක කොහෙද?",
        "මගේ CEFTS transfer එක තාම pending.",
    ],
}

TAMIL_MESSAGES = {
    "account_balance": [
        "எனது கணக்கு இருப்பு எவ்வளவு?",
        "எனது account balance ஐ பார்க்க முடியுமா?",
    ],
    "recent_transactions": [
        "எனது கடைசி 5 transactions ஐ காட்டுங்கள்.",
        "எனது சமீபத்திய transactions பார்க்க வேண்டும்.",
    ],
    "payment_declined": [
        "எனது payment ஏன் declined ஆனது?",
        "எனது card payment தோல்வியடைந்தது.",
    ],
    "lost_card": [
        "எனது card தொலைந்து விட்டது.",
        "எனது debit card கிடைக்கவில்லை.",
    ],
    "block_card": [
        "எனது card ஐ block செய்யுங்கள்.",
        "தயவுசெய்து எனது card ஐ block செய்யவும்.",
    ],
    "refund_status": [
        "எனது refund எங்கே?",
        "எனது refund இன்னும் வரவில்லை.",
    ],
    "loan_balance": [
        "எனது loan balance எவ்வளவு?",
        "எனது loan க்கு இன்னும் எவ்வளவு செலுத்த வேண்டும்?",
    ],
    "make_payment": [
        "நான் ஒரு payment செய்ய விரும்புகிறேன்.",
        "நான் பணம் transfer செய்ய வேண்டும்.",
    ],
    "complaint": [
        "ஒரு transaction பற்றி complaint செய்ய வேண்டும்.",
        "எனது account பற்றி புகார் உள்ளது.",
    ],
    "cefts_transfer": [
        "எனது CEFTS transfer எங்கே?",
        "எனது CEFTS transfer இன்னும் pending.",
    ],
}

KNOWLEDGE_DOCUMENTS = [
    (
        "KYC Requirements",
        "kyc",
        """KYC Requirements for Sri Lankan Banking Customers

Customers may be required to provide a valid national identity document,
passport, proof of address, and other supporting information depending on
the banking service. Customer information must be verified before sensitive
account operations are completed."""
    ),
    (
        "Lost or Stolen Card Procedure",
        "card_security",
        """Lost or Stolen Card Procedure

Customers should immediately report a lost or stolen debit or credit card.
The bank may temporarily block or permanently block the card after
authentication. Customers should never share their PIN, OTP, CVV, or
online banking password with another person."""
    ),
    (
        "CEFTS Transfers",
        "payments",
        """CEFTS Transfer Information

CEFTS enables electronic fund transfers between participating Sri Lankan
financial institutions. Transfer processing may depend on the receiving
institution, transaction status, banking hours, and applicable controls.
Customers should provide the transaction reference when requesting support."""
    ),
    (
        "Refund Processing",
        "refunds",
        """Refund Processing

A merchant refund may take time to appear in a customer's account.
Customers should retain the merchant refund reference and transaction
details. Support agents can investigate a refund using the transaction
reference, merchant name, amount, and transaction date."""
    ),
    (
        "Account Balance and Transactions",
        "accounts",
        """Account Balance and Transaction Information

Customers can request their current and available balance after successful
authentication. Recent transactions may include purchases, deposits,
withdrawals, transfers, salary credits, fees, refunds, and interest."""
    ),
    (
        "Loan Payments",
        "loans",
        """Loan Payment Information

Loan payments may contain principal and interest components. Customers can
request outstanding balances, installment schedules, due dates, and payment
status after authentication."""
    ),
    (
        "Security and Authentication",
        "security",
        """Security and Authentication

Sensitive banking operations require appropriate authentication and
authorization. The AI assistant must not reveal confidential credentials,
full card numbers, PINs, CVVs, passwords, or raw national identification
numbers. High-risk operations should require additional verification."""
    ),
]


# ============================================================
# HELPERS
# ============================================================

def new_uuid() -> str:
    return str(uuid.uuid4())


def money(value) -> Decimal:
    return Decimal(str(value)).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def random_money(low: float, high: float) -> Decimal:
    value = random.uniform(low, high)
    return money(value)


def random_date(start: date, end: date) -> date:
    if end <= start:
        return start

    days = (end - start).days
    return start + timedelta(days=random.randint(0, days))


def random_datetime(start: date, end: date) -> datetime:
    d = random_date(start, end)
    return datetime(
        d.year,
        d.month,
        d.day,
        random.randint(0, 23),
        random.randint(0, 59),
        random.randint(0, 59),
    )


def sql_quote(value):
    """
    Convert Python values to safe SQL literals.
    """
    if value is None:
        return "NULL"

    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"

    if isinstance(value, Decimal):
        return str(value)

    if isinstance(value, datetime):
        return "'" + value.isoformat(sep=" ") + "'"

    if isinstance(value, date):
        return "'" + value.isoformat() + "'"

    if isinstance(value, (dict, list)):
        text = json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        text = text.replace("'", "''")
        return f"'{text}'::jsonb"

    text = str(value).replace("'", "''")
    return f"'{text}'"


def sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def distribute(total: int, minimum: int, count: int):
    """
    Distribute 'total' records across 'count' parents.
    """
    result = [minimum] * count
    remaining = total - (minimum * count)

    while remaining > 0:
        index = random.randrange(count)
        result[index] += 1
        remaining -= 1

    return result


def choose_weighted_status():
    return random.choices(
        ["active", "blocked", "inactive"],
        weights=[88, 7, 5],
        k=1,
    )[0]


# ============================================================
# NAME GENERATION
# ============================================================

def generate_person_name(index: int):
    group = random.choices(
        ["sinhala_male", "sinhala_female", "tamil", "muslim"],
        weights=[38, 35, 15, 12],
        k=1,
    )[0]

    if group == "sinhala_male":
        return (
            random.choice(MALE_FIRST_NAMES),
            random.choice(SINHALA_SURNAMES),
        )

    if group == "sinhala_female":
        return (
            random.choice(FEMALE_FIRST_NAMES),
            random.choice(SINHALA_SURNAMES),
        )

    if group == "tamil":
        full = random.choice(TAMIL_NAMES)
        parts = full.split()

        if len(parts) == 1:
            return parts[0], "Raj"

        return parts[0], " ".join(parts[1:])

    full = random.choice(MUSLIM_NAMES)
    parts = full.split()

    if len(parts) == 1:
        return parts[0], "Mohamed"

    return parts[0], " ".join(parts[1:])


# ============================================================
# SQL BUILDER
# ============================================================

class SQLBuilder:
    def __init__(self):
        self.lines = []

    def comment(self, text: str):
        self.lines.append(f"-- {text}")

    def raw(self, text: str):
        self.lines.append(text)

    def insert(self, table: str, columns: list[str], values: list):
        values_sql = ", ".join(sql_quote(v) for v in values)

        self.lines.append(
            f"INSERT INTO {table} ({', '.join(columns)}) "
            f"VALUES ({values_sql});"
        )

    def extend(self, statements):
        self.lines.extend(statements)

    def build(self):
        return "\n".join(self.lines) + "\n"


# ============================================================
# MAIN GENERATOR
# ============================================================

def generate():
    print("Generating synthetic Sri Lankan banking dataset...")
    print(f"Output: {OUTPUT_FILE}")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    sql = SQLBuilder()

    sql.comment("Synthetic Banking AI Customer Service SaaS Seed")
    sql.comment(f"Generated with deterministic seed: {SEED}")
    sql.comment("All personal/card identifiers are synthetic.")
    sql.raw("BEGIN;")
    sql.raw("SET LOCAL statement_timeout = '5min';")
    sql.raw("")

    # --------------------------------------------------------
    # SAFETY GUARD
    # --------------------------------------------------------

    sql.raw(
        """
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM tenant
        WHERE tenant_code = 'SLBANK01'
    ) THEN
        RAISE EXCEPTION
            'Synthetic tenant SLBANK01 already exists. Do not run this seed twice.';
    END IF;
END $$;
""".strip()
    )

    # --------------------------------------------------------
    # TENANT
    # --------------------------------------------------------

    tenant_id = new_uuid()

    sql.comment("1. TENANT")

    sql.insert(
        "tenant",
        [
            "id",
            "tenant_code",
            "legal_name",
            "display_name",
            "status",
            "default_currency",
        ],
        [
            tenant_id,
            TENANT_CODE,
            TENANT_NAME,
            "Lanka Digital Bank",
            "active",
            "LKR",
        ],
    )

    # --------------------------------------------------------
    # CUSTOMERS
    # --------------------------------------------------------

    sql.comment("2. CUSTOMERS")

    customers = []
    customer_emails = set()
    customer_phones = set()

    for i in range(1, NUM_CUSTOMERS + 1):
        customer_id = new_uuid()

        first_name, last_name = generate_person_name(i)

        email_base = (
            f"{first_name}.{last_name}"
            .lower()
            .replace(" ", "")
        )

        email = f"{email_base}{i}@example.com"

        while email in customer_emails:
            email = f"{email_base}{random.randint(1000, 9999)}@example.com"

        customer_emails.add(email)

        while True:
            phone = f"07{random.randint(0, 8)}{random.randint(1000000, 9999999)}"
            if phone not in customer_phones:
                customer_phones.add(phone)
                break

        # Synthetic old/new NIC
        if random.random() < 0.45:
            nic_raw = (
                f"{random.randint(100000000, 999999999)}"
                f"{random.choice(['V', 'X'])}"
            )
        else:
            nic_raw = str(random.randint(195000000000, 200999999999))

        nic_hash = sha256(nic_raw)

        dob = date(
            random.randint(1965, 2005),
            random.randint(1, 12),
            random.randint(1, 28),
        )

        status = choose_weighted_status()

        customers.append(
            {
                "id": customer_id,
                "customer_number": f"CUST{i:06d}",
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "phone": phone,
                "dob": dob,
                "national_id_hash": nic_hash,
                "status": status,
            }
        )

        sql.insert(
            "customer",
            [
                "id",
                "tenant_id",
                "customer_number",
                "first_name",
                "last_name",
                "email",
                "phone",
                "date_of_birth",
                "national_id_hash",
                "status",
            ],
            [
                customer_id,
                tenant_id,
                f"CUST{i:06d}",
                first_name,
                last_name,
                email,
                phone,
                dob,
                nic_hash,
                status,
            ],
        )

    # --------------------------------------------------------
    # APP USERS
    # --------------------------------------------------------

    sql.comment("3. APPLICATION USERS")

    app_users = []
    support_users = []

    # Customer users
    for i, customer in enumerate(customers, start=1):
        user_id = new_uuid()

        if customer["status"] == "active":
            user_status = "active"
        elif customer["status"] == "blocked":
            user_status = "locked"
        else:
            user_status = "disabled"

        app_users.append(
            {
                "id": user_id,
                "customer_id": customer["id"],
                "email": customer["email"],
            }
        )

        sql.insert(
            "app_user",
            [
                "id",
                "tenant_id",
                "customer_id",
                "external_subject",
                "email",
                "password_hash",
                "first_name",
                "last_name",
                "status",
            ],
            [
                user_id,
                tenant_id,
                customer["id"],
                f"cognito-{new_uuid()}",
                customer["email"],
                sha256(f"synthetic-password-{i}"),
                customer["first_name"],
                customer["last_name"],
                user_status,
            ],
        )

        sql.raw(
            f"""
INSERT INTO user_role (user_id, role_id)
SELECT
    '{user_id}',
    r.id
FROM role r
WHERE r.tenant_id IS NULL
  AND r.role_code = 'customer';
""".strip()
        )

    # Support/admin users
    support_names = [
        ("Amal", "Fernando", "support"),
        ("Nadeesha", "Perera", "support"),
        ("Ruwan", "Jayasinghe", "support"),
        ("Shalini", "Rathnayake", "support"),
    ]

    for i, (first_name, last_name, role_code) in enumerate(
        support_names,
        start=1,
    ):
        user_id = new_uuid()
        email = (
            f"{first_name.lower()}.{last_name.lower()}"
            f"@lankadigitalbank.example"
        )

        support_user = {
            "id": user_id,
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
        }

        support_users.append(support_user)

        sql.insert(
            "app_user",
            [
                "id",
                "tenant_id",
                "customer_id",
                "external_subject",
                "email",
                "password_hash",
                "first_name",
                "last_name",
                "status",
            ],
            [
                user_id,
                tenant_id,
                None,
                f"support-{new_uuid()}",
                email,
                sha256(f"synthetic-support-password-{i}"),
                first_name,
                last_name,
                "active",
            ],
        )

        sql.raw(
            f"""
INSERT INTO user_role (user_id, role_id)
SELECT
    '{user_id}',
    r.id
FROM role r
WHERE r.tenant_id IS NULL
  AND r.role_code = 'support_agent';
""".strip()
        )

    # --------------------------------------------------------
    # ACCOUNTS
    # --------------------------------------------------------

    sql.comment("4. ACCOUNTS")

    accounts = []

    customer_account_counts = distribute(
        NUM_ACCOUNTS,
        1,
        NUM_CUSTOMERS,
    )

    account_counter = 0

    for customer, count in zip(customers, customer_account_counts):

        for _ in range(count):
            account_counter += 1

            account_id = new_uuid()

            account_type = random.choices(
                ACCOUNT_TYPES,
                weights=[55, 20, 15, 10],
                k=1,
            )[0]

            opened = random_date(
                date(2023, 1, 1),
                date(2026, 5, 1),
            )

            if customer["status"] == "active":
                account_status = random.choices(
                    ["active", "dormant", "blocked", "closed"],
                    weights=[78, 8, 8, 6],
                    k=1,
                )[0]
            else:
                account_status = random.choice(
                    ["blocked", "dormant", "closed"]
                )

            if account_type == "fixed_deposit":
                opening_balance = random_money(100000, 5000000)
            else:
                opening_balance = random_money(5000, 500000)

            closed_at = None
            if account_status == "closed":
                opening_balance = Decimal("0.00")
                closed_at = random_datetime(opened, TODAY)

            account = {
                "id": account_id,
                "customer_id": customer["id"],
                "account_number": f"001{account_counter:010d}",
                "account_type": account_type,
                "opened": opened,
                "status": account_status,
                "balance": opening_balance,
                "available_balance": opening_balance,
            }

            accounts.append(account)

            sql.insert(
                "account",
                [
                    "id",
                    "tenant_id",
                    "customer_id",
                    "account_number",
                    "account_type",
                    "currency",
                    "current_balance",
                    "available_balance",
                    "status",
                    "opened_at",
                    "closed_at",
                ],
                [
                    account_id,
                    tenant_id,
                    customer["id"],
                    account["account_number"],
                    account_type,
                    "LKR",
                    opening_balance,
                    opening_balance,
                    account_status,
                    opened,
                    closed_at,
                ],
            )

    # --------------------------------------------------------
    # ACCOUNT TRANSACTIONS
    # --------------------------------------------------------

    sql.comment("5. ACCOUNT TRANSACTIONS")

    eligible_accounts = [a for a in accounts if a["status"] != "closed"]

    transaction_counts = distribute(
        NUM_ACCOUNT_TRANSACTIONS,
        5,
        len(eligible_accounts),
    )

    transaction_counter = 0

    for account, count in zip(eligible_accounts, transaction_counts):

        balance = account["balance"]

        events = []

        for _ in range(count):
            transaction_counter += 1

            transaction_at = random_datetime(
                account["opened"],
                TODAY,
            )

            tx_type = random.choices(
                ACCOUNT_TRANSACTION_TYPES,
                weights=[
                    28,  # purchase
                    12,  # cash withdrawal
                    12,  # deposit
                    12,  # transfer
                    10,  # salary
                    8,   # bill
                    5,   # fee
                    4,   # refund
                    5,   # interest
                    4,   # other
                ],
                k=1,
            )[0]

            if tx_type in {
                "deposit",
                "salary",
                "refund",
                "interest",
            }:
                direction = "credit"

                if tx_type == "salary":
                    amount = random_money(45000, 350000)
                    description = "Monthly salary credit"
                    merchant = None

                elif tx_type == "interest":
                    amount = random_money(100, 25000)
                    description = "Interest credit"
                    merchant = None

                elif tx_type == "refund":
                    amount = random_money(500, 75000)
                    description = "Merchant refund"
                    merchant = random.choice(MERCHANTS)

                else:
                    amount = random_money(1000, 200000)
                    description = "Cash deposit"
                    merchant = None

                balance += amount

            else:
                direction = "debit"

                if tx_type == "purchase":
                    amount = random_money(250, 75000)
                    merchant = random.choice(MERCHANTS)
                    description = f"POS purchase - {merchant}"

                elif tx_type == "cash_withdrawal":
                    amount = random_money(1000, 100000)
                    merchant = None
                    description = "ATM cash withdrawal"

                elif tx_type == "bill_payment":
                    amount = random_money(1000, 50000)
                    merchant = random.choice(BILL_MERCHANTS)
                    description = f"Utility bill payment - {merchant}"

                elif tx_type == "fee":
                    amount = random_money(50, 5000)
                    merchant = None
                    description = "Bank service fee"

                elif tx_type == "transfer":
                    amount = random_money(1000, 150000)
                    merchant = random.choice(BANKS)
                    description = "Bank transfer / CEFTS"

                else:
                    amount = random_money(100, 10000)
                    merchant = None
                    description = "Banking transaction"

                # Never allow balance below zero.
                if amount > balance:
                    amount = money(
                        max(
                            Decimal("0.00"),
                            balance * Decimal("0.40"),
                        )
                    )

                balance -= amount

            balance = money(max(balance, Decimal("0.00")))

            events.append(
                {
                    "id": new_uuid(),
                    "transaction_number": f"ATX-2026-{transaction_counter:08d}",
                    "transaction_at": transaction_at,
                    "transaction_type": tx_type,
                    "amount": amount,
                    "direction": direction,
                    "balance_after": balance,
                    "description": description,
                    "merchant_name": merchant,
                }
            )

        # Sort transactions chronologically so balance_after makes sense.
        events.sort(key=lambda x: x["transaction_at"])

        # Recalculate balances chronologically.
        running_balance = account["balance"]

        for event in events:
            if event["direction"] == "credit":
                running_balance += event["amount"]
            else:
                running_balance -= event["amount"]

            running_balance = money(
                max(running_balance, Decimal("0.00"))
            )

            event["balance_after"] = running_balance

            sql.insert(
                "account_transaction",
                [
                    "id",
                    "tenant_id",
                    "account_id",
                    "transaction_number",
                    "transaction_type",
                    "amount",
                    "currency",
                    "direction",
                    "balance_after",
                    "description",
                    "merchant_name",
                    "transaction_at",
                ],
                [
                    event["id"],
                    tenant_id,
                    account["id"],
                    event["transaction_number"],
                    event["transaction_type"],
                    event["amount"],
                    "LKR",
                    event["direction"],
                    event["balance_after"],
                    event["description"],
                    event["merchant_name"],
                    event["transaction_at"],
                ],
            )

        account["balance"] = running_balance
        account["available_balance"] = running_balance

        sql.raw(
            f"""
UPDATE account
SET
    current_balance = {sql_quote(running_balance)},
    available_balance = {sql_quote(running_balance)}
WHERE id = {sql_quote(account["id"])};
""".strip()
        )

    # --------------------------------------------------------
    # CARDS
    # --------------------------------------------------------

    sql.comment("6. CARDS")

    cards = []
    used_card_hashes = set()

    for i in range(1, NUM_CARDS + 1):

        customer = random.choice(customers)
        card_id = new_uuid()

        while True:
            fake_pan = "9999" + str(random.randint(100000000000, 999999999999))
            fake_pan = fake_pan[:16]

            card_hash = sha256(fake_pan)

            if card_hash not in used_card_hashes:
                used_card_hashes.add(card_hash)
                break

        last4 = fake_pan[-4:]

        issued = random_date(
            date(2023, 1, 1),
            date(2026, 5, 1),
        )

        expiry = issued.replace(
            year=issued.year + random.choice([3, 4, 5])
        )

        card_type = random.choices(
            ["debit", "credit", "prepaid"],
            weights=[70, 25, 5],
            k=1,
        )[0]

        status = random.choices(
            ["active", "blocked", "expired"],
            weights=[82, 10, 8],
            k=1,
        )[0]

        if status == "expired":
            expiry = random_date(date(2024, 1, 1), TODAY - timedelta(days=1))

        blocked_at = None
        if status == "blocked":
            blocked_at = random_datetime(issued, TODAY)

        card = {
            "id": card_id,
            "customer_id": customer["id"],
            "card_hash": card_hash,
            "last4": last4,
            "issued": issued,
            "expiry": expiry,
            "type": card_type,
            "status": status,
        }

        cards.append(card)

        sql.insert(
            "card",
            [
                "id",
                "tenant_id",
                "customer_id",
                "card_number_hash",
                "card_last4",
                "card_type",
                "expiry_month",
                "expiry_year",
                "status",
                "daily_limit",
                "issued_at",
                "blocked_at",
            ],
            [
                card_id,
                tenant_id,
                customer["id"],
                card_hash,
                last4,
                card_type,
                expiry.month,
                expiry.year,
                status,
                random_money(50000, 1000000),
                issued,
                blocked_at,
            ],
        )

    # --------------------------------------------------------
    # CARD TRANSACTIONS
    # --------------------------------------------------------

    sql.comment("7. CARD TRANSACTIONS")

    card_tx_counter = 0

    for _ in range(NUM_CARD_TRANSACTIONS):

        card = random.choice(cards)

        card_tx_counter += 1

        transaction_at = random_datetime(
            card["issued"],
            TODAY,
        )

        status = random.choices(
            [
                "completed",
                "pending",
                "declined",
                "reversed",
            ],
            weights=[78, 8, 9, 5],
            k=1,
        )[0]

        merchant = random.choice(MERCHANTS)

        sql.insert(
            "card_transaction",
            [
                "id",
                "tenant_id",
                "card_id",
                "transaction_number",
                "amount",
                "currency",
                "merchant_name",
                "merchant_category",
                "status",
                "transaction_at",
            ],
            [
                new_uuid(),
                tenant_id,
                card["id"],
                f"CTX-2026-{card_tx_counter:08d}",
                random_money(250, 100000),
                "LKR",
                merchant,
                random.choice(TRANSACTION_CATEGORIES),
                status,
                transaction_at,
            ],
        )

    # --------------------------------------------------------
    # LOANS
    # --------------------------------------------------------

    sql.comment("8. LOANS")

    loans = []

    for i in range(1, NUM_LOANS + 1):

        customer = random.choice(customers)

        loan_id = new_uuid()

        loan_type = random.choice(LOAN_TYPES)

        start_date = random_date(
            date(2024, 1, 1),
            date(2026, 7, 1),
        )

        maturity_date = start_date + timedelta(
            days=random.choice([365, 730, 1095, 1825, 3650])
        )

        principal = random_money(
            {
                "personal": (100000, 2000000),
                "home": (3000000, 25000000),
                "vehicle": (1000000, 12000000),
                "education": (250000, 3000000),
                "business": (2000000, 20000000),
            }[loan_type][0],
            {
                "personal": (100000, 2000000),
                "home": (3000000, 25000000),
                "vehicle": (1000000, 12000000),
                "education": (250000, 3000000),
                "business": (2000000, 20000000),
            }[loan_type][1],
        )

        status = random.choices(
            ["active", "closed", "defaulted", "pending"],
            weights=[65, 20, 8, 7],
            k=1,
        )[0]

        if status == "closed":
            outstanding = Decimal("0.00")
        elif status == "pending":
            outstanding = Decimal("0.00")
        else:
            outstanding = money(
                principal * Decimal(
                    str(random.uniform(0.15, 0.85))
                )
            )

        loan = {
            "id": loan_id,
            "customer_id": customer["id"],
            "loan_number": f"LN{i:06d}",
            "loan_type": loan_type,
            "principal": principal,
            "outstanding": outstanding,
            "interest_rate": Decimal(
                str(round(random.uniform(7.5, 18.5), 2))
            ),
            "status": status,
            "start_date": start_date,
            "maturity_date": maturity_date,
        }

        loans.append(loan)

        sql.insert(
            "loan",
            [
                "id",
                "tenant_id",
                "customer_id",
                "loan_number",
                "loan_type",
                "principal_amount",
                "outstanding_amount",
                "interest_rate",
                "currency",
                "status",
                "start_date",
                "maturity_date",
            ],
            [
                loan_id,
                tenant_id,
                customer["id"],
                loan["loan_number"],
                loan_type,
                principal,
                outstanding,
                loan["interest_rate"],
                "LKR",
                status,
                start_date,
                maturity_date,
            ],
        )

    # --------------------------------------------------------
    # LOAN PAYMENTS - EXACTLY 500
    # --------------------------------------------------------

    sql.comment("9. LOAN PAYMENTS")

    payment_counter = 0

    for loan in loans:

        # Exactly 10 installments per loan = 500.
        for installment in range(1, 11):

            payment_counter += 1

            payment_id = new_uuid()

            due_date = loan["start_date"] + timedelta(
                days=30 * installment
            )

            installment_amount = money(
                max(
                    Decimal("5000"),
                    loan["principal"] / Decimal("24"),
                )
            )

            principal_component = money(
                installment_amount * Decimal("0.70")
            )

            interest_component = money(
                installment_amount - principal_component
            )

            if loan["status"] == "closed":
                status = "paid"
                paid_date = due_date
            elif due_date < TODAY:
                status = random.choices(
                    ["paid", "overdue"],
                    weights=[85, 15],
                    k=1,
                )[0]

                paid_date = (
                    due_date + timedelta(days=random.randint(0, 15))
                    if status == "paid"
                    else None
                )
            else:
                status = random.choice(
                    ["scheduled", "cancelled"]
                )
                paid_date = None

            sql.insert(
                "loan_payment",
                [
                    "id",
                    "tenant_id",
                    "loan_id",
                    "payment_number",
                    "installment_number",
                    "amount",
                    "principal_component",
                    "interest_component",
                    "currency",
                    "due_date",
                    "paid_at",
                    "status",
                ],
                [
                    payment_id,
                    tenant_id,
                    loan["id"],
                    f"LNP-{payment_counter:07d}",
                    installment,
                    installment_amount,
                    principal_component,
                    interest_component,
                    "LKR",
                    due_date,
                    paid_date,
                    status,
                ],
            )

    # --------------------------------------------------------
    # BENEFICIARIES
    # --------------------------------------------------------

    sql.comment("10. BENEFICIARIES")

    beneficiaries = []

    for i in range(1, NUM_BENEFICIARIES + 1):

        customer = random.choice(customers)

        beneficiary_id = new_uuid()

        first_name, last_name = generate_person_name(i)

        beneficiary = {
            "id": beneficiary_id,
            "customer_id": customer["id"],
            "beneficiary_number": f"BEN{i:06d}",
            "name": f"{first_name} {last_name}",
            "bank": random.choice(BANKS),
        }

        beneficiaries.append(beneficiary)

        masked_account = (
            f"****{random.randint(1000, 9999)}"
        )

        status = random.choices(
            ["active", "blocked", "deleted"],
            weights=[88, 8, 4],
            k=1,
        )[0]

        sql.insert(
            "beneficiary",
            [
                "id",
                "tenant_id",
                "customer_id",
                "beneficiary_number",
                "beneficiary_name",
                "bank_name",
                "account_number_masked",
                "status",
            ],
            [
                beneficiary_id,
                tenant_id,
                customer["id"],
                beneficiary["beneficiary_number"],
                beneficiary["name"],
                beneficiary["bank"],
                masked_account,
                status,
            ],
        )

    # --------------------------------------------------------
    # PAYMENTS
    # --------------------------------------------------------

    sql.comment("11. PAYMENTS")

    active_beneficiaries = [
        b for b in beneficiaries
    ]

    active_accounts = [
        a for a in accounts
        if a["status"] == "active"
    ]

    active_accounts_with_beneficiaries = [
        a for a in active_accounts
        if any(b["customer_id"] == a["customer_id"] for b in active_beneficiaries)
    ]

    for i in range(1, NUM_PAYMENTS + 1):

        if not active_accounts_with_beneficiaries:
            break

        source_account = random.choice(active_accounts_with_beneficiaries)

        customer_id = source_account["customer_id"]

        customer_beneficiaries = [
            b for b in active_beneficiaries
            if b["customer_id"] == customer_id
        ]

        beneficiary = random.choice(customer_beneficiaries)

        payment_status = random.choices(
            [
                "completed",
                "pending",
                "processing",
                "failed",
                "cancelled",
            ],
            weights=[62, 12, 8, 10, 8],
            k=1,
        )[0]

        sql.insert(
            "payment",
            [
                "id",
                "tenant_id",
                "customer_id",
                "source_account_id",
                "beneficiary_id",
                "payment_number",
                "amount",
                "currency",
                "payment_reference",
                "status",
                "idempotency_key",
                "requested_at",
                "completed_at",
            ],
            [
                new_uuid(),
                tenant_id,
                customer_id,
                source_account["id"],
                beneficiary["id"],
                f"PAY-{i:07d}",
                random_money(1000, 250000),
                "LKR",
                f"REF-{uuid.uuid4().hex[:12].upper()}",
                payment_status,
                f"idem-{uuid.uuid4()}",
                random_datetime(
                    date(2025, 1, 1),
                    TODAY,
                ),
                (
                    random_datetime(
                        date(2025, 1, 1),
                        TODAY,
                    )
                    if payment_status == "completed"
                    else None
                ),
            ],
        )

    # --------------------------------------------------------
    # COMPLAINTS
    # --------------------------------------------------------

    sql.comment("12. COMPLAINTS")

    complaint_categories = [
        "card",
        "transaction",
        "payment",
        "account",
        "loan",
        "refund",
        "transfer",
        "service",
    ]

    for i in range(1, NUM_COMPLAINTS + 1):

        customer = random.choice(customers)
        support = random.choice(support_users)

        sql.insert(
            "complaint",
            [
                "id",
                "tenant_id",
                "customer_id",
                "complaint_number",
                "category",
                "priority",
                "subject",
                "description",
                "status",
                "assigned_to",
            ],
            [
                new_uuid(),
                tenant_id,
                customer["id"],
                f"CMP-{i:06d}",
                random.choice(complaint_categories),
                random.choice(["low", "medium", "high", "critical"]),
                random.choice([
                    "Incorrect transaction",
                    "Card payment issue",
                    "Refund not received",
                    "Transfer problem",
                    "Account service issue",
                ]),
                random.choice([
                    "Customer reported an unexpected banking transaction.",
                    "Customer reported that a card payment failed.",
                    "Customer has not received an expected refund.",
                    "Customer reported a delayed transfer.",
                    "Customer requested investigation of an account issue.",
                ]),
                random.choice([
                    "open",
                    "in_progress",
                    "resolved",
                    "closed",
                ]),
                support["id"],
            ],
        )

    # --------------------------------------------------------
    # SUPPORT TICKETS
    # --------------------------------------------------------

    sql.comment("13. SUPPORT TICKETS")

    ticket_categories = [
        "technical",
        "account",
        "card",
        "payment",
        "loan",
        "general",
    ]

    for i in range(1, NUM_TICKETS + 1):

        customer = random.choice(customers)
        support = random.choice(support_users)

        sql.insert(
            "support_ticket",
            [
                "id",
                "tenant_id",
                "customer_id",
                "ticket_number",
                "category",
                "priority",
                "subject",
                "description",
                "status",
                "assigned_to",
            ],
            [
                new_uuid(),
                tenant_id,
                customer["id"],
                f"TKT-{i:06d}",
                random.choice(ticket_categories),
                random.choice(["low", "medium", "high"]),
                random.choice([
                    "Unable to complete payment",
                    "Card assistance required",
                    "Account balance question",
                    "Loan information request",
                    "Transfer status request",
                    "General banking assistance",
                ]),
                "Synthetic customer support ticket created for testing.",
                random.choice([
                    "open",
                    "in_progress",
                    "resolved",
                    "closed",
                ]),
                support["id"],
            ],
        )

    # --------------------------------------------------------
    # CONVERSATIONS
    # --------------------------------------------------------

    sql.comment("14. AI CONVERSATIONS")

    conversations = []

    for i in range(1, NUM_CONVERSATIONS + 1):

        customer = random.choice(customers)

        conversation_id = new_uuid()

        channel = random.choice(
            ["web", "mobile", "api", "whatsapp", "voice"]
        )

        intent = random.choice(INTENTS)

        start = random_datetime(
            date(2026, 1, 1),
            TODAY,
        )

        status = random.choices(
            ["active", "closed", "escalated"],
            weights=[15, 65, 20],
            k=1,
        )[0]

        end = (
            start + timedelta(minutes=random.randint(2, 30))
            if status != "active"
            else None
        )

        conversations.append(
            {
                "id": conversation_id,
                "customer_id": customer["id"],
                "intent": intent,
                "start": start,
                "status": status,
            }
        )

        sql.insert(
            "conversation",
            [
                "id",
                "tenant_id",
                "customer_id",
                "conversation_number",
                "channel",
                "status",
                "title",
                "summary",
                "started_at",
                "ended_at",
            ],
            [
                conversation_id,
                tenant_id,
                customer["id"],
                f"CONV-{i:06d}",
                channel,
                status,
                intent.replace("_", " ").title(),
                f"Synthetic conversation regarding {intent.replace('_', ' ')}.",
                start,
                end,
            ],
        )

    # --------------------------------------------------------
    # MESSAGES
    # --------------------------------------------------------

    sql.comment("15. CONVERSATION MESSAGES")

    messages_per_conversation = distribute(
        NUM_MESSAGES,
        3,
        NUM_CONVERSATIONS,
    )

    message_counter = 0

    for conversation, count in zip(
        conversations,
        messages_per_conversation,
    ):

        intent = conversation["intent"]

        for j in range(count):

            message_counter += 1

            language = random.choices(
                ["en", "si", "ta"],
                weights=[65, 25, 10],
                k=1,
            )[0]

            if language == "si":
                messages = SINHALA_MESSAGES.get(
                    intent,
                    SINHALA_MESSAGES["account_balance"],
                )
            elif language == "ta":
                messages = TAMIL_MESSAGES.get(
                    intent,
                    TAMIL_MESSAGES["account_balance"],
                )
            else:
                messages = ENGLISH_MESSAGES.get(
                    intent,
                    ENGLISH_MESSAGES["account_balance"],
                )

            if j % 2 == 0:
                sender_type = "customer"
                content = random.choice(messages)
                model_name = None
            else:
                sender_type = "assistant"

                content = random.choice([
                    "I can help you with that. Please complete the required authentication first.",
                    "I can check the transaction details after successful authentication.",
                    "For security, I need to verify your identity before performing this operation.",
                    "I can provide the relevant banking information once the request is authorized.",
                ])

                model_name = random.choice([
                    "gpt-banking-assistant",
                    "banking-rag-assistant",
                    "support-agent-v1",
                ])

            sql.insert(
                "message",
                [
                    "id",
                    "tenant_id",
                    "conversation_id",
                    "sender_type",
                    "content",
                    "intent",
                    "model_name",
                    "token_count",
                ],
                [
                    new_uuid(),
                    tenant_id,
                    conversation["id"],
                    sender_type,
                    content,
                    intent,
                    model_name,
                    random.randint(10, 150),
                ],
            )

    # --------------------------------------------------------
    # TOOL EXECUTIONS
    # --------------------------------------------------------

    sql.comment("16. AI TOOL EXECUTIONS")

    tool_names = [
        "get_account_balance",
        "get_recent_transactions",
        "get_card_status",
        "block_card",
        "get_refund_status",
        "get_loan_balance",
        "get_payment_status",
        "create_payment",
        "create_complaint",
        "get_cefts_status",
    ]

    for i in range(1, NUM_TOOL_EXECUTIONS + 1):

        customer = random.choice(customers)
        user = next(
            (
                u for u in app_users
                if u["customer_id"] == customer["id"]
            ),
            None,
        )

        tool_name = random.choice(tool_names)

        risk_level = (
            "high"
            if tool_name in {
                "block_card",
                "create_payment",
                "create_complaint",
            }
            else "low"
        )

        status = random.choices(
            ["succeeded", "failed", "denied"],
            weights=[82, 10, 8],
            k=1,
        )[0]

        authorization_result = (
            "approved"
            if status == "succeeded"
            else random.choice([
                "validation_failed",
                "authorization_failed",
                "system_error",
            ])
        )

        sql.insert(
            "tool_execution",
            [
                "id",
                "tenant_id",
                "user_id",
                "conversation_id",
                "tool_name",
                "risk_level",
                "status",
                "authorization_result",
                "idempotency_key",
                "request_payload",
                "response_payload",
                "error_message",
                "correlation_id",
            ],
            [
                new_uuid(),
                tenant_id,
                user["id"] if user else None,
                random.choice(conversations)["id"],
                tool_name,
                risk_level,
                status,
                authorization_result,
                f"tool-{uuid.uuid4()}",
                {
                    "customer_id": customer["id"],
                    "synthetic": True,
                },
                {
                    "success": status == "succeeded",
                    "synthetic": True,
                },
                None if status == "succeeded" else "Synthetic tool execution failure",
                str(uuid.uuid4()),
            ],
        )

    # --------------------------------------------------------
    # AUDIT LOGS
    # --------------------------------------------------------

    sql.comment("17. AUDIT LOGS")

    audit_actions = [
        "LOGIN",
        "LOGOUT",
        "VIEW_ACCOUNT",
        "VIEW_TRANSACTION",
        "VIEW_CARD",
        "BLOCK_CARD",
        "CREATE_PAYMENT",
        "VIEW_LOAN",
        "CREATE_COMPLAINT",
        "AI_TOOL_EXECUTION",
    ]

    resource_types = [
        "customer",
        "account",
        "transaction",
        "card",
        "loan",
        "payment",
        "complaint",
        "conversation",
    ]

    for _ in range(NUM_AUDIT_LOGS):

        user_choice = random.choice(
            app_users + [
                {
                    "id": s["id"],
                    "customer_id": None,
                }
                for s in support_users
            ]
        )

        success = random.choices(
            [True, False],
            weights=[94, 6],
            k=1,
        )[0]

        sql.insert(
            "audit_log",
            [
                "id",
                "tenant_id",
                "actor_user_id",
                "action",
                "resource_type",
                "resource_id",
                "correlation_id",
                "ip_address",
                "user_agent",
                "success",
                "metadata",
            ],
            [
                new_uuid(),
                tenant_id,
                user_choice["id"],
                random.choice(audit_actions),
                random.choice(resource_types),
                new_uuid(),
                str(uuid.uuid4()),
                f"192.0.2.{random.randint(1, 254)}",
                random.choice([
                    "Mozilla/5.0 Synthetic Banking Client",
                    "Banking-Mobile-App/1.0",
                    "Banking-API-Client/1.0",
                ]),
                success,
                {
                    "synthetic": True,
                    "source": "seed_generator",
                },
            ],
        )

    # --------------------------------------------------------
    # RAG DOCUMENTS
    # --------------------------------------------------------

    sql.comment("18. RAG KNOWLEDGE DOCUMENTS")

    for i, (title, doc_type, content) in enumerate(
        KNOWLEDGE_DOCUMENTS,
        start=1,
    ):

        document_id = new_uuid()
        version_id = new_uuid()
        chunk_id = new_uuid()

        document_key = (
            title.lower()
            .replace(" ", "-")
            .replace("/", "-")
        )

        sql.insert(
            "document",
            [
                "id",
                "tenant_id",
                "document_key",
                "title",
                "document_type",
                "status",
                "owner_user_id",
            ],
            [
                document_id,
                tenant_id,
                document_key,
                title,
                doc_type,
                "published",
                support_users[0]["id"],
            ],
        )

        sql.insert(
            "document_version",
            [
                "id",
                "tenant_id",
                "document_id",
                "version_number",
                "content_hash",
                "status",
                "effective_from",
                "approved_at",
                "approved_by",
                "published_at",
            ],
            [
                version_id,
                tenant_id,
                document_id,
                1,
                sha256(content),
                "published",
                date(2026, 1, 1),
                datetime(2026, 1, 1, 9, 0, 0),
                support_users[0]["id"],
                datetime(2026, 1, 1, 10, 0, 0),
            ],
        )

        sql.insert(
            "document_chunk",
            [
                "id",
                "tenant_id",
                "document_id",
                "document_version_id",
                "chunk_index",
                "content",
                "content_hash",
                "token_count",
                "metadata",
                "embedding",
            ],
            [
                chunk_id,
                tenant_id,
                document_id,
                version_id,
                0,
                content,
                sha256(content),
                len(content.split()),
                {
                    "document_type": doc_type,
                    "language": "en",
                    "synthetic": True,
                },
                None,
            ],
        )

    # --------------------------------------------------------
    # FINISH
    # --------------------------------------------------------

    sql.raw("")
    sql.comment("Synthetic seed generation completed.")
    sql.raw("COMMIT;")

    OUTPUT_FILE.write_text(
        sql.build(),
        encoding="utf-8",
    )

    print("")
    print("SUCCESS")
    print("=======")
    print(f"SQL seed file created:")
    print(OUTPUT_FILE)
    print("")
    print(f"Customers:             {len(customers)}")
    print(f"Accounts:              {len(accounts)}")
    print(f"Cards:                 {len(cards)}")
    print(f"Loans:                 {len(loans)}")
    print(f"Beneficiaries:         {len(beneficiaries)}")
    print(f"Conversations:         {len(conversations)}")
    print(f"RAG documents:         {len(KNOWLEDGE_DOCUMENTS)}")
    print("")
    print("The generated SQL has NOT been loaded into PostgreSQL yet.")


if __name__ == "__main__":
    generate()


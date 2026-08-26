import json
import random
from collections import Counter
from datetime import datetime, timedelta, timezone


random.seed(42)

OUTPUT_FILE = "data/failed_payments.json"
RECORD_COUNT = 56

MERCHANT_IDS = [
    "merch_grocerly",
    "merch_fitpass",
    "merch_edulearn",
    "merch_medkart",
    "merch_travelio",
    "merch_stylehub",
    "merch_cloudbooks",
    "merch_foodlane",
]

FIRST_NAMES = [
    "Aarav",
    "Vivaan",
    "Aditya",
    "Ishaan",
    "Ananya",
    "Diya",
    "Meera",
    "Riya",
    "Kabir",
    "Neha",
    "Arjun",
    "Kavya",
]

LAST_NAMES = [
    "Sharma",
    "Verma",
    "Iyer",
    "Nair",
    "Mehta",
    "Kapoor",
    "Reddy",
    "Gupta",
    "Joshi",
    "Malhotra",
    "Das",
    "Bose",
]

PAYMENT_METHODS = ["card", "upi", "netbanking", "wallet"]
PAYMENT_METHOD_WEIGHTS = [38, 34, 18, 10]

FAILURE_REASONS = [
    "insufficient_funds",
    "issuer_declined",
    "invalid_otp",
    "bank_timeout",
    "gateway_error",
    "expired_card",
    "network_error",
]
FAILURE_REASON_WEIGHTS = [28, 22, 16, 13, 10, 7, 4]

ATTEMPT_COUNTS = [1, 2, 3]
ATTEMPT_COUNT_WEIGHTS = [72, 21, 7]

SUBSCRIPTION_VALUES = [True, False]
SUBSCRIPTION_WEIGHTS = [25, 75]


def pick_failure_reason(index):
    if index <= len(FAILURE_REASONS):
        return FAILURE_REASONS[index - 1]

    return random.choices(FAILURE_REASONS, weights=FAILURE_REASON_WEIGHTS, k=1)[0]


def make_customer(index):
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)
    name = f"{first_name} {last_name}"
    email = f"{first_name.lower()}.{last_name.lower()}{index}@example.com"
    phone = f"+91{random.randint(7000000000, 9999999999)}"
    return name, email, phone


def make_amount():
    price_bands = [
        (199, 999),
        (1000, 4999),
        (5000, 11999),
        (12000, 25000),
    ]
    band = random.choices(price_bands, weights=[35, 38, 18, 9], k=1)[0]
    base_amount = random.randint(band[0], band[1])
    return base_amount + random.choice([0, 9, 19, 25, 49, 75, 99])


def make_timestamps(now, attempt_count):
    first_failed_at = now - timedelta(
        days=random.randint(0, 13),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
    )

    if attempt_count == 1:
        return first_failed_at.isoformat(), first_failed_at.isoformat()

    hours_between_attempts = random.randint(6, 36)
    retry_jitter = random.randint(-45, 45)
    retry_gap = timedelta(hours=hours_between_attempts, minutes=retry_jitter)
    last_attempt_at = first_failed_at + retry_gap * (attempt_count - 1)

    if last_attempt_at > now:
        last_attempt_at = now - timedelta(minutes=random.randint(1, 90))

    return first_failed_at.isoformat(), last_attempt_at.isoformat()


def generate_records():
    now = datetime.now(timezone.utc).replace(microsecond=0)
    records = []

    for index in range(1, RECORD_COUNT + 1):
        customer_name, customer_email, customer_phone = make_customer(index)
        attempt_count = random.choices(
            ATTEMPT_COUNTS, weights=ATTEMPT_COUNT_WEIGHTS, k=1
        )[0]
        first_failed_at, last_attempt_at = make_timestamps(now, attempt_count)

        record = {
            "record_id": f"fail_{index:04d}",
            "order_id": f"order_{100000 + index}",
            "merchant_id": random.choice(MERCHANT_IDS),
            "customer_name": customer_name,
            "customer_email": customer_email,
            "customer_phone": customer_phone,
            "amount": make_amount(),
            "payment_method": random.choices(
                PAYMENT_METHODS, weights=PAYMENT_METHOD_WEIGHTS, k=1
            )[0],
            "failure_reason": pick_failure_reason(index),
            "attempt_count": attempt_count,
            "first_failed_at": first_failed_at,
            "last_attempt_at": last_attempt_at,
            "is_subscription": random.choices(
                SUBSCRIPTION_VALUES, weights=SUBSCRIPTION_WEIGHTS, k=1
            )[0],
        }
        records.append(record)

    return records


def print_summary(records):
    total_amount = sum(record["amount"] for record in records)
    reason_counts = Counter(record["failure_reason"] for record in records)

    print(f"Generated {len(records)} failed payment records")
    print(f"Total amount at stake: INR {total_amount:,}")
    print("Records per failure reason:")

    for reason, count in reason_counts.most_common():
        print(f"- {reason}: {count}")


def main():
    records = generate_records()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(records, file, indent=2)

    print(f"Wrote {OUTPUT_FILE}")
    print_summary(records)


if __name__ == "__main__":
    main()

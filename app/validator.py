REQUIRED_FIELDS = {
    "record_id",
    "order_id",
    "merchant_id",
    "customer_name",
    "customer_email",
    "customer_phone",
    "amount",
    "payment_method",
    "failure_reason",
    "attempt_count",
    "first_failed_at",
    "last_attempt_at",
    "is_subscription",
}


def validate_record(record):
    missing_fields = REQUIRED_FIELDS - record.keys()
    if missing_fields:
        raise ValueError(f"Missing fields: {sorted(missing_fields)}")

    return True

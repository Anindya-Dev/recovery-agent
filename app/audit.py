def build_audit_entry(record, action):
    return {
        "record_id": record["record_id"],
        "order_id": record["order_id"],
        "failure_reason": record["failure_reason"],
        "action": action,
        "amount": record["amount"],
        "attempt_count": record["attempt_count"],
    }

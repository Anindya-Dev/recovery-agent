def decide_action(record):
    failure_reason = record["failure_reason"]
    attempt_count = record["attempt_count"]

    if failure_reason in {"bank_timeout", "gateway_error", "network_error"}:
        return "retry_now" if attempt_count == 1 else "retry_later"

    if failure_reason in {"insufficient_funds", "expired_card", "invalid_otp"}:
        return "send_payment_link"

    return "escalate_to_human"

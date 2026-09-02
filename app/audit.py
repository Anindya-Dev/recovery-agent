import json
from pathlib import Path

from .models import FailedPayment, RecoveryDecision


AUDIT_PATH = Path(__file__).parent.parent / "data" / "audit_log.json"


def build_audit_entry(
    payment: FailedPayment,
    decision: RecoveryDecision,
    source: str,
    validator_overridden: bool,
) -> dict:
    return {
        "record_id": payment.record_id,
        "order_id": payment.order_id,
        "failure_reason": payment.failure_reason,
        "amount": payment.amount,
        "attempt_count": payment.attempt_count,
        "source": source,
        "action": decision.action.value,
        "reasoning": decision.reasoning,
        "confidence": decision.confidence,
        "retry_delay_minutes": decision.retry_delay_minutes,
        "validator_overridden": validator_overridden,
    }


def save_audit_entry(entry: dict) -> None:
    if AUDIT_PATH.exists():
        with open(AUDIT_PATH, "r", encoding="utf-8") as file:
            entries = json.load(file)
    else:
        entries = []

    entries.append(entry)

    with open(AUDIT_PATH, "w", encoding="utf-8") as file:
        json.dump(entries, file, indent=2)
from .models import FailedPayment, RecoveryDecision
from .classifier import decide
from .llm import llm_decide
from .validator import validate_decision
from .audit import build_audit_entry, save_audit_entry


def recover_payment(payment: FailedPayment) -> RecoveryDecision:
    try:
        decision = decide(payment)
        source = "classifier"

    except ValueError:
        decision = llm_decide(payment)
        source = "llm"

    original_action = decision.action

    decision = validate_decision(payment, decision)

    validator_overridden = (
        decision.action != original_action
    )

    audit_entry = build_audit_entry(
        payment=payment,
        decision=decision,
        source=source,
        validator_overridden=validator_overridden,
    )

    save_audit_entry(audit_entry)

    print(f"AUDIT: {audit_entry}")

    return decision

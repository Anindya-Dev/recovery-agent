from .models import FailedPayment, RecoveryDecision, RecoveryAction
from .razorpay_client import create_payment_link


def execute_decision(
    payment: FailedPayment,
    decision: RecoveryDecision,
) -> dict:

    if decision.action == RecoveryAction.RETRY_NOW:
        return {
            "record_id": payment.record_id,
            "action": decision.action.value,
            "status": "simulated",
            "message": "Payment retry would be triggered now.",
        }

    if decision.action == RecoveryAction.RETRY_DELAYED:
        return {
            "record_id": payment.record_id,
            "action": decision.action.value,
            "status": "simulated",
            "message": (
                f"Payment retry would be scheduled after "
                f"{decision.retry_delay_minutes} minutes."
            ),
        }

    if decision.action == RecoveryAction.SEND_PAYMENT_LINK:
        payment_link = create_payment_link(payment)

        return {
            "record_id": payment.record_id,
            "action": decision.action.value,
            "status": "success",
            "payment_link": payment_link,
            "message": "Razorpay payment link created successfully.",
        }

    if decision.action == RecoveryAction.ESCALATE_TO_HUMAN:
        return {
            "record_id": payment.record_id,
            "action": decision.action.value,
            "status": "pending",
            "message": "Payment recovery case escalated to a human.",
        }

    raise ValueError(f"Unsupported recovery action: {decision.action}")
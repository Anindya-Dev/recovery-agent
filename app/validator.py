from .models import FailedPayment, RecoveryDecision, RecoveryAction

def validate_decision(
        payment: FailedPayment,
        decision: RecoveryDecision,
        )-> RecoveryDecision:
    if payment.attempt_count>=3:
        return RecoveryDecision(
            record_id=payment.record_id,
            action=RecoveryAction.ESCALATE_TO_HUMAN,
            reasoning=(
                f"Payment has reached {payment.attempt_count} attempts. "
                "Automatic recovery is not allowed beyond the retry limit."
            ),
            confidence=1.0,
            retry_delay_minutes=None,
        )
    if decision.action==RecoveryAction.RETRY_NOW:
        delay=decision.retry_delay_minutes

        if delay is not None and not 1 <= delay <= 20:
            return RecoveryDecision(
                record_id=payment.record_id,
                action=RecoveryAction.ESCALATE_TO_HUMAN,
                reasoning=(
                   "The LLM recommended an immediate retry with an invalid "
                    "retry delay. The allowed delay is either None or between "
                    "1 and 20 minutes, so the decision was overridden for safety."
                ),
                confidence=1.0,
                retry_delay_minutes=None,
            )
    if decision.action == RecoveryAction.RETRY_DELAYED:
        delay= decision.retry_delay_minutes

        if delay is None or not 30 <= delay <= 1440:
            return RecoveryDecision(
                record_id=payment.record_id,
                action=RecoveryAction.ESCALATE_TO_HUMAN,
                reasoning=(
                    "The LLM recommended a delayed retry with an invalid "
                    "retry delay. The allowed delay is between 30 minutes "
                    "and 24 hours, so the decision was overridden for safety."
                ),
                confidence=1.0,
                retry_delay_minutes=None,
            )
    if decision.action in (
        RecoveryAction.SEND_PAYMENT_LINK,
        RecoveryAction.ESCALATE_TO_HUMAN,
    ):
        if decision.retry_delay_minutes is not None:
            return RecoveryDecision(
                record_id=payment.record_id,
                action=RecoveryAction.ESCALATE_TO_HUMAN,
                reasoning=(
                    "The decision contains a retry delay even though the "
                    "selected action does not perform a retry. The decision "
                    "was overridden for safety."
                ),
                confidence=1.0,
                retry_delay_minutes=None,
            )
    return decision

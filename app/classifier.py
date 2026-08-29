from .models import FailedPayment, RecoveryDecision, RecoveryAction

def decide(payment: FailedPayment)-> RecoveryDecision:
    if payment.attempt_count>=3:
        return RecoveryDecision(
            record_id=payment.record_id,
            action=RecoveryAction.ESCALATE_TO_HUMAN,
            reasoning=(f"Payment has reached {payment.attempt_count} attempts, "
                       "so automated recovery is stopped and the case is escalated to a human."),
            confidence=1.0,
        )
    if payment.failure_reason in ("issuer_declined","gateway_error"): #Ambiguos-reason block
        raise ValueError(
            f"Ambiguous failure reason: {payment.failure_reason}. "
            "This case must be handled by the LLM."
        )
    if payment.failure_reason == "insufficient_funds":
        if payment.attempt_count<2:
            return RecoveryDecision(
                record_id=payment.record_id,
                action=RecoveryAction.RETRY_DELAYED, 
                reasoning=("Payment failed due to insufficient funds and this is the "
                           "customer's first attempt, so the payment will be retried after 24 hours."),
                confidence=1.0,
                retry_delay_minutes=1440
            )
        else:
            return RecoveryDecision(
                record_id=payment.record_id,
                action=RecoveryAction.SEND_PAYMENT_LINK,
                reasoning=("Payment failed due to insufficient funds after multiple attempts, "
                           "so a payment link is provided instead of continuing automatic retries."),
                confidence=1.0
            )
    if payment.failure_reason =="expired_card":
        return RecoveryDecision(
            record_id=payment.record_id,
            action=RecoveryAction.SEND_PAYMENT_LINK,
            reasoning=("The customer's card has expired, so retrying the same payment "
                       "method is unlikely to succeed. A payment link provides an alternative."),
            confidence=1.0,
        )
    if payment.failure_reason=="bank_timeout":
        return RecoveryDecision(
            record_id=payment.record_id,
            action=RecoveryAction.RETRY_NOW, # RETRY_NOW: retry_delay_minutes can be None or between 1 and 20 minutes
            reasoning=("The payment failed because of a temporary bank timeout, "
                       "so retrying after a short delay may succeed."),
            confidence=1.0,
            retry_delay_minutes=10
        )
    if payment.failure_reason=="network_error":
        return RecoveryDecision(
            record_id=payment.record_id,
            action=RecoveryAction.RETRY_NOW,
            reasoning=("The payment failed because of a temporary network error, "
                       "so retrying after a short delay may succeed."),
            confidence=1.0,
            retry_delay_minutes=15
        )
    if payment.failure_reason=="invalid_otp":
        return RecoveryDecision(
            record_id=payment.record_id,
            action=RecoveryAction.RETRY_NOW,
            reasoning=("The payment failed because of an invalid OTP, "
                       "so the customer should be given a short delay before retrying."),
            confidence=1.0,
            retry_delay_minutes=1

        )
    raise ValueError(
    f"Unsupported failure reason: {payment.failure_reason}"
)


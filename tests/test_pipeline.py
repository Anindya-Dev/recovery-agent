from datetime import datetime

from app.models import FailedPayment, RecoveryAction
from app.pipeline import recover_payment


def test_pipeline_handles_ambiguous_failure_with_llm():
    payment = FailedPayment(
        record_id="pipeline_llm_001",
        order_id="order_001",
        merchant_id="merchant_001",
        customer_name="Test User",
        customer_email="test@example.com",
        customer_phone="9999999999",
        amount=821.0,
        payment_method="card",
        failure_reason="issuer_declined",
        attempt_count=1,
        first_failed_at=datetime.now(),
        last_attempt_at=datetime.now(),
        is_subscription=False,
    )

    decision = recover_payment(payment)

    assert decision.record_id == "pipeline_llm_001"
    assert decision.action in (
        RecoveryAction.RETRY_NOW,
        RecoveryAction.RETRY_DELAYED,
        RecoveryAction.SEND_PAYMENT_LINK,
        RecoveryAction.ESCALATE_TO_HUMAN,
    )

    assert 0.0 <= decision.confidence <= 1.0
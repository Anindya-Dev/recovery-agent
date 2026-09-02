from datetime import datetime
from unittest.mock import patch

from app.models import FailedPayment, RecoveryAction, RecoveryDecision
from app.pipeline import recover_payment


@patch("app.pipeline.save_audit_entry")
@patch("app.pipeline.llm_decide")
def test_pipeline_handles_ambiguous_failure_with_llm(mock_llm_decide, mock_save_audit_entry):
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

    mock_llm_decide.return_value = RecoveryDecision(
        record_id="pipeline_llm_001",
        action=RecoveryAction.RETRY_NOW,
        reasoning="Issuer decline can be retried once.",
        confidence=0.85,
        retry_delay_minutes=5,
    )

    decision = recover_payment(payment)

    assert decision.record_id == "pipeline_llm_001"
    assert decision.action == RecoveryAction.RETRY_NOW
    assert 0.0 <= decision.confidence <= 1.0
    mock_llm_decide.assert_called_once_with(payment)
    mock_save_audit_entry.assert_called_once()

from datetime import datetime
from unittest.mock import patch

from app.models import FailedPayment, RecoveryDecision, RecoveryAction
from app.executor import execute_decision


def make_payment():
    return FailedPayment(
        record_id="executor_test_001",
        order_id="order_test_001",
        merchant_id="merchant_test_001",
        customer_name="Test Customer",
        customer_email="test@example.com",
        customer_phone="9123456780",
        amount=100.0,
        payment_method="card",
        failure_reason="insufficient_funds",
        attempt_count=2,
        first_failed_at=datetime.now(),
        last_attempt_at=datetime.now(),
        is_subscription=False,
    )
def test_execute_retry_now():
    payment = make_payment()

    decision = RecoveryDecision(
        record_id=payment.record_id,
        action=RecoveryAction.RETRY_NOW,
        reasoning="Temporary failure.",
        confidence=0.9,
        retry_delay_minutes=10,
    )

    result = execute_decision(payment, decision)

    assert result["action"] == "retry_now"
    assert result["status"] == "simulated"

def test_execute_retry_delayed():
    payment = make_payment()

    decision = RecoveryDecision(
        record_id=payment.record_id,
        action=RecoveryAction.RETRY_DELAYED,
        reasoning="Retry later.",
        confidence=0.9,
        retry_delay_minutes=60,
    )

    result = execute_decision(payment, decision)

    assert result["action"] == "retry_delayed"
    assert result["status"] == "simulated"

def test_execute_escalation():
    payment = make_payment()

    decision = RecoveryDecision(
        record_id=payment.record_id,
        action=RecoveryAction.ESCALATE_TO_HUMAN,
        reasoning="Too many attempts.",
        confidence=1.0,
        retry_delay_minutes=None,
    )

    result = execute_decision(payment, decision)

    assert result["action"] == "escalate_to_human"
    assert result["status"] == "pending"

@patch("app.executor.create_payment_link")
def test_execute_payment_link(mock_create_link):
    mock_create_link.return_value = "https://rzp.io/test-link"

    payment = make_payment()

    decision = RecoveryDecision(
        record_id=payment.record_id,
        action=RecoveryAction.SEND_PAYMENT_LINK,
        reasoning="Alternative payment method needed.",
        confidence=0.9,
        retry_delay_minutes=None,
    )

    result = execute_decision(payment, decision)

    mock_create_link.assert_called_once_with(payment)

    assert result["action"] == "send_payment_link"
    assert result["status"] == "success"
    assert result["payment_link"] == "https://rzp.io/test-link"

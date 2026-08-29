from datetime import datetime

from app.models import FailedPayment,RecoveryDecision,RecoveryAction
from app.validator import validate_decision

def make_payment(attempt_count=1):
    return FailedPayment(
        record_id="test_001",
        order_id="order_001",
        merchant_id="merchant_001",
        customer_name="Test User",
        customer_email="test@example.com",
        customer_phone="9999999999",
        amount=500.0,
        payment_method="card",
        failure_reason="gateway_error",
        attempt_count=attempt_count,
        first_failed_at=datetime.now(),
        last_attempt_at=datetime.now(),
        is_subscription=False,
    )

def test_three_attempts_always_escalate(): # 1 — 3 attempts must escalate
    payment = make_payment(attempt_count=3)

    decision = RecoveryDecision(
        record_id="test_001",
        action=RecoveryAction.RETRY_NOW,
        reasoning="LLM wants to retry.",
        confidence=0.9,
        retry_delay_minutes=None,
    )

    result = validate_decision(payment, decision)

    assert result.action == RecoveryAction.ESCALATE_TO_HUMAN
    assert result.retry_delay_minutes is None

def test_retry_now_invalid_delay(): # invalid RETRY_NOW delay
    payment = make_payment()

    decision = RecoveryDecision(
        record_id="test_001",
        action=RecoveryAction.RETRY_NOW,
        reasoning="Retry immediately.",
        confidence=0.9,
        retry_delay_minutes=25,
    )

    result = validate_decision(payment, decision)

    assert result.action == RecoveryAction.ESCALATE_TO_HUMAN

def test_valid_retry_delayed(): # valid delayed retry
    payment = make_payment()

    decision = RecoveryDecision(
        record_id="test_001",
        action=RecoveryAction.RETRY_DELAYED,
        reasoning="Retry later.",
        confidence=0.9,
        retry_delay_minutes=60,
    )

    result = validate_decision(payment, decision)

    assert result.action == RecoveryAction.RETRY_DELAYED
    assert result.retry_delay_minutes == 60
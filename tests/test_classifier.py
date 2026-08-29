from app.classifier import decide
from app.models import FailedPayment, RecoveryAction
from datetime import datetime
import pytest

@pytest.mark.parametrize(
    "failure_reason,attempt_count,expected_action",
    [
        ("insufficient_funds", 1, RecoveryAction.RETRY_DELAYED),
        ("insufficient_funds", 2, RecoveryAction.SEND_PAYMENT_LINK),
        ("expired_card", 1, RecoveryAction.SEND_PAYMENT_LINK),
        ("bank_timeout", 1, RecoveryAction.RETRY_NOW),
        ("network_error", 1, RecoveryAction.RETRY_NOW),
        ("invalid_otp", 1, RecoveryAction.RETRY_NOW),
    ],

)

def test_rule_based_decisions(
    failure_reason,
    attempt_count,
    expected_action,
):
    payment = FailedPayment(
        record_id="test_001",
        order_id="order_001",
        merchant_id="merchant_001",
        customer_name="Test User",
        customer_email="test@example.com",
        customer_phone="9999999999",
        amount=500.0,
        payment_method="card",
        failure_reason=failure_reason,
        attempt_count=attempt_count,
        first_failed_at=datetime.now(),
        last_attempt_at=datetime.now(),
        is_subscription=False,
    )

    decision = decide(payment)

    assert decision.action == expected_action

def test_three_or_more_attempts_always_escalates():
    payment = FailedPayment(
        record_id="test_002",
        order_id="order_002",
        merchant_id="merchant_001",
        customer_name="Test User",
        customer_email="test@example.com",
        customer_phone="9999999999",
        amount=500.0,
        payment_method="card",
        failure_reason="insufficient_funds",
        attempt_count=3,
        first_failed_at=datetime.now(),
        last_attempt_at=datetime.now(),
        is_subscription=False,
    )

    decision = decide(payment)

    assert decision.action == RecoveryAction.ESCALATE_TO_HUMAN

@pytest.mark.parametrize(
    "failure_reason",
    ["issuer_declined", "gateway_error"],
)
def test_ambiguous_reasons_raise_error(failure_reason):
    payment = FailedPayment(
        record_id="test_003",
        order_id="order_003",
        merchant_id="merchant_001",
        customer_name="Test User",
        customer_email="test@example.com",
        customer_phone="9999999999",
        amount=500.0,
        payment_method="card",
        failure_reason=failure_reason,
        attempt_count=1,
        first_failed_at=datetime.now(),
        last_attempt_at=datetime.now(),
        is_subscription=False,
    )

    with pytest.raises(ValueError):
        decide(payment)
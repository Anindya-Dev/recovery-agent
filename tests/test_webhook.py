from unittest.mock import patch

from fastapi.testclient import TestClient

from app.models import RecoveryAction, RecoveryDecision
from app.webhook import app


client = TestClient(app)


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@patch("app.webhook.recover_payment")
def test_payment_failed_webhook_returns_recovery_decision(mock_recover_payment):
    mock_recover_payment.return_value = RecoveryDecision(
        record_id="pay_test_001",
        action=RecoveryAction.SEND_PAYMENT_LINK,
        reasoning="Expired card needs a fresh payment link.",
        confidence=1.0,
        retry_delay_minutes=None,
    )

    response = client.post(
        "/webhooks/razorpay/payment-failed",
        json={
            "account_id": "merchant_test_001",
            "payload": {
                "payment": {
                    "entity": {
                        "id": "pay_test_001",
                        "order_id": "order_test_001",
                        "amount": 10000,
                        "method": "card",
                        "error_reason": "expired_card",
                        "attempt_count": 1,
                        "created_at": 1788201000,
                        "email": "test@example.com",
                        "contact": "9123456780",
                        "customer_name": "Test Customer",
                    }
                }
            },
        },
    )

    assert response.status_code == 200
    assert response.json()["record_id"] == "pay_test_001"
    assert response.json()["action"] == "send_payment_link"
    mock_recover_payment.assert_called_once()

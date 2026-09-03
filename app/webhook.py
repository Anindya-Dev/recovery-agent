from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, HTTPException

from .models import FailedPayment
from .pipeline import recover_payment


app = FastAPI(title="recovery-agent")


def payment_from_webhook(payload: dict[str, Any]) -> FailedPayment:
    payment_entity = (
        payload.get("payload", {})
        .get("payment", {})
        .get("entity", {})
    )

    if not payment_entity:
        raise HTTPException(status_code=400, detail="Missing payment entity")

    failed_at = datetime.fromtimestamp(
        payment_entity.get("created_at", datetime.now(timezone.utc).timestamp()),
        tz=timezone.utc,
    )

    error_reason = (
        payment_entity.get("error_reason")
        or payment_entity.get("error_code")
        or "gateway_error"
    )

    return FailedPayment(
        record_id=payment_entity.get("id", "unknown_payment"),
        order_id=payment_entity.get("order_id", "unknown_order"),
        merchant_id=payload.get("account_id", "unknown_merchant"),
        customer_name=payment_entity.get("customer_name", "Unknown Customer"),
        customer_email=payment_entity.get("email", "unknown@example.com"),
        customer_phone=payment_entity.get("contact", "9000000000"),
        amount=payment_entity.get("amount", 0) / 100,
        payment_method=payment_entity.get("method", "card"),
        failure_reason=error_reason,
        attempt_count=payment_entity.get("attempt_count", 1),
        first_failed_at=failed_at,
        last_attempt_at=failed_at,
        is_subscription=bool(payment_entity.get("subscription_id")),
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/webhooks/razorpay/payment-failed")
def handle_payment_failed(payload: dict[str, Any]) -> dict[str, Any]:
    payment = payment_from_webhook(payload)
    decision = recover_payment(payment)

    return {
        "record_id": payment.record_id,
        "order_id": payment.order_id,
        "action": decision.action.value,
        "reasoning": decision.reasoning,
        "confidence": decision.confidence,
        "retry_delay_minutes": decision.retry_delay_minutes,
    }

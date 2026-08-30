from datetime import datetime

from app.llm import llm_decide
from app.models import FailedPayment


payment = FailedPayment(
    record_id="fail_0002",
    order_id="order_0005",
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

decision = llm_decide(payment)

print(decision)

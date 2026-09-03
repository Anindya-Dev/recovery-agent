from datetime import datetime

from app.models import FailedPayment
from app.razorpay_client import create_payment_link


if __name__ == "__main__":
    payment = FailedPayment(
        record_id=f"razorpay_test_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        order_id=f"order_test_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        merchant_id="merchant_test_001",
        customer_name="Test Customer",
        customer_email="test@example.com",
        customer_phone="9123456788",
        amount=100.0,
        payment_method="card",
        failure_reason="insufficient_funds",
        attempt_count=2,
        first_failed_at=datetime.now(),
        last_attempt_at=datetime.now(),
        is_subscription=False,
    )

    url = create_payment_link(payment)

    print("\nPayment Link created:")
    print(url)

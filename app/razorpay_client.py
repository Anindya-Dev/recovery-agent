import os

import razorpay
from dotenv import load_dotenv

from .models import FailedPayment


load_dotenv()


client = razorpay.Client(
    auth=(
        os.getenv("RAZORPAY_KEY_ID"),
        os.getenv("RAZORPAY_KEY_SECRET"),
    )
)


def create_payment_link(payment: FailedPayment) -> str:
    data = {
        "amount": int(payment.amount * 100),
        "currency": "INR",
        "accept_partial": False,
        "reference_id": payment.record_id,
        "description": f"Payment recovery for order {payment.order_id}",
        "customer": {
            "name": payment.customer_name,
            "contact": payment.customer_phone,
            "email": payment.customer_email,
        },
        "notify": {
            "sms": True,
            "email": True,
        },
        "reminder_enable": True,
    }

    payment_link = client.payment_link.create(data)

    return payment_link["short_url"]
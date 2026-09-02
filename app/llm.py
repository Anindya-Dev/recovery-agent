import json
import os 

from openai import OpenAI
from dotenv import load_dotenv

from .models import FailedPayment, RecoveryDecision

load_dotenv()


client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("NVIDIA_API_KEY"),
)

RECOVERY_DECISION_SCHEMA = {
    "type": "object",
    "properties": {
        "record_id": {"type": "string"},
        "action": {
            "type": "string",
            "enum": [
                "retry_now",
                "retry_delayed",
                "send_payment_link",
                "escalate_to_human",
            ],
        },
        "reasoning": {
            "type": "string",
            "maxLength": 160,
        },
        "confidence": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0,
        },
        "retry_delay_minutes": {
            "anyOf": [
                {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 1440,
                },
                {"type": "null"},
            ],
        },
    },
    "required": [
        "record_id",
        "action",
        "reasoning",
        "confidence",
        "retry_delay_minutes",
    ],
    "additionalProperties": False,
}

def llm_decide(payment: FailedPayment)-> RecoveryDecision:
    system_prompt = """
You are a payment recovery decision assistant.

Your job is to recommend the safest recovery action for a failed payment.

You may choose only one of these actions:
- retry_now
- retry_delayed
- send_payment_link
- escalate_to_human

Consider the payment failure reason, amount, attempt count,
payment method, and subscription status.

Never recommend an automatic retry when attempt_count is 3 or more.

Return ONLY a valid JSON object.
Do not include markdown.
Do not include ```json.
Do not include your thinking process.
Do not include any text before or after the JSON.

The JSON must contain exactly these fields:
record_id
action
reasoning
confidence
retry_delay_minutes

action must be exactly one of:
"retry_now"
"retry_delayed"
"send_payment_link"
"escalate_to_human"

confidence must be a number between 0.0 and 1.0.

reasoning must be one short sentence under 20 words.
Do not explain step by step.
Do not include analysis.

If action is "retry_now", retry_delay_minutes must be null or an integer between 1 and 20.

If action is "retry_delayed", retry_delay_minutes must be an integer between 30 and 1440.

If action is "send_payment_link" or "escalate_to_human",
retry_delay_minutes must be null.

Base your reasoning only on the payment information provided.

Return exactly this shape:
{
  "record_id": "same record_id from input",
  "action": "retry_now",
  "reasoning": "one short sentence under 20 words",
  "confidence": 0.8,
  "retry_delay_minutes": 10
}
"""
    payment_data={
        "record_id": payment.record_id,
        "amount": payment.amount,
        "payment_method": payment.payment_method,
        "failure_reason": payment.failure_reason,
        "attempt_count": payment.attempt_count,
        "first_failed_at": payment.first_failed_at.isoformat(),
        "last_attempt_at": payment.last_attempt_at.isoformat(),
        "is_subscription": payment.is_subscription,
    }

    response=client.chat.completions.create(
        model="nvidia/nemotron-3.5-lightning-30b-a3b",
        messages=[
            {
                "role":"system",
                "content":system_prompt,
            },
            {
                "role":"user",
                "content":json.dumps(payment_data),
            },
        ],
        temperature=0.2,
        max_tokens=500,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "recovery_decision",
                "schema": RECOVERY_DECISION_SCHEMA,
            },
        },
        extra_body={
            "chat_template_kwargs":{
                "enable_thinking":False
            }
        }
    )
    content= response.choices[0].message.content
    result=json.loads(content)
    decision = RecoveryDecision(**result)
    return decision

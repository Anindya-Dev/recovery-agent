# recovery-agent

`recovery-agent` is a payment recovery agent built for Razorpay's AI Builder Internship 2026, Track 3: AI Revenue Recovery. Failed payments are often treated as terminal events even when many of them are recoverable: a customer may only need a later retry, a fresh payment link, or a small amount of manual support. This project turns failed payment records into explainable recovery actions, executes those actions through Razorpay test-mode APIs, and produces an audit trail that shows what was attempted, why it was attempted, and how much revenue was recovered.

## Architecture

The agent runs as a simple four-stage pipeline:

1. **Data**: Load a batch of failed payment records with amount, customer, failure message, payment id, and metadata.
2. **Classifier**: Assign each record a normalized failure reason such as `insufficient_funds`, `expired_card`, `bank_timeout`, `gateway_error`, `invalid_otp`, `issuer_declined`, or `network_error`.
3. **Executor**: Choose and run the recovery action: retry now, retry later, send a payment link, or escalate to a human.
4. **Audit/report**: Store every decision with its reason, Razorpay response, status, and recovered amount.

## How the classifier decides

The classifier uses deterministic rules for failure reasons that can be identified reliably from Razorpay error codes or stable message patterns. For example, expired cards, invalid OTPs, and insufficient funds usually have clear signals, so rules are faster, cheaper, and easier to audit.

Ambiguous records are sent to an LLM call using the Anthropic API. This is used when the gateway message is vague, inconsistent, or missing structured fields. The split keeps common cases predictable while still allowing the agent to reason over messy real-world failure text.

## Setup

Install dependencies:

```bash
npm install
```

Create a `.env` file:

```bash
RAZORPAY_KEY_ID=rzp_test_your_key_id
RAZORPAY_KEY_SECRET=your_test_key_secret
ANTHROPIC_API_KEY=sk-ant-your_key
```

Run the agent against the sample batch:

```bash
npm run start
```

Run tests:

```bash
npm test
```

Expected input shape:

```json
[
  {
    "payment_id": "pay_test_001",
    "customer_id": "cust_001",
    "amount": 2500,
    "currency": "INR",
    "failure_code": "BAD_REQUEST_ERROR",
    "failure_description": "Payment failed due to insufficient funds",
    "attempt_count": 1
  }
]
```

## Sample output

Example recovery report from a local test-mode run:

```json
{
  "batch_id": "batch_2026_08_23_001",
  "total_failed_amount": 187500,
  "total_recovered_amount": 72500,
  "recovery_rate": "38.67%",
  "records_processed": 12,
  "actions": {
    "retry_now": 3,
    "retry_later": 4,
    "send_payment_link": 3,
    "escalate_to_human": 2
  },
  "by_failure_reason": {
    "insufficient_funds": {
      "count": 3,
      "recovered_amount": 25000,
      "unresolved": 1
    },
    "expired_card": {
      "count": 2,
      "recovered_amount": 15000,
      "unresolved": 1
    },
    "bank_timeout": {
      "count": 2,
      "recovered_amount": 20000,
      "unresolved": 0
    },
    "gateway_error": {
      "count": 2,
      "recovered_amount": 12500,
      "unresolved": 0
    },
    "invalid_otp": {
      "count": 1,
      "recovered_amount": 0,
      "unresolved": 1
    },
    "issuer_declined": {
      "count": 1,
      "recovered_amount": 0,
      "unresolved": 1
    },
    "network_error": {
      "count": 1,
      "recovered_amount": 0,
      "unresolved": 0
    }
  },
  "unresolved_cases": [
    {
      "payment_id": "pay_test_004",
      "failure_reason": "issuer_declined",
      "action": "escalate_to_human",
      "reason": "Issuer declined the payment and automatic retries are unlikely to succeed."
    },
    {
      "payment_id": "pay_test_009",
      "failure_reason": "invalid_otp",
      "action": "send_payment_link",
      "reason": "Customer authentication failed; a fresh payment link was generated but not completed."
    }
  ]
}
```

Each record also produces an audit entry:

```json
{
  "payment_id": "pay_test_003",
  "classified_as": "bank_timeout",
  "classifier": "rule",
  "action": "retry_later",
  "decision_reason": "Bank timeout is usually transient, but immediate retry can duplicate load on the issuer.",
  "razorpay_request_id": "req_test_abc123",
  "result": "recovered",
  "recovered_amount": 20000
}
```

## Design decisions and trade-offs

- **Rules before LLM**: Common failure reasons are handled with deterministic rules because they are cheaper, faster, and easier to explain during an audit.
- **LLM only for ambiguous cases**: The LLM is used when structured failure data is incomplete or unclear. This keeps the system flexible without making every decision dependent on a model call.
- **Retries are capped**: Automatic retries stop after a small number of attempts to avoid duplicate charges, customer frustration, and noisy gateway traffic.
- **Idempotency is required**: Every recovery action uses stable identifiers so the same failed payment cannot accidentally trigger duplicate payment links, duplicate retries, or inconsistent audit records.

## What I'd build next

- Extend the same pipeline to checkout abandonment, where the system can decide whether to send reminders, payment links, or support follow-ups.
- Add receivables recovery for unpaid invoices, including reminder timing, customer segmentation, and escalation rules.
- Improve reporting with cohort-level recovery metrics so merchants can see which failure reasons, banks, and payment methods create the most recoverable loss.

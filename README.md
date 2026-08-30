# recovery-agent

`recovery-agent` is a Python payment-recovery agent built for Razorpay's AI Builder Internship 2026, Track 3: AI Revenue Recovery. Failed payments are direct revenue leakage: the customer intended to pay, the merchant expected the money, but the transaction failed somewhere in the payment flow. This project processes a batch of failed payment records, classifies the failure, selects a bounded recovery action, validates that action against safety rules, and prints a recovery summary. The goal is not just to retry payments, but to make every decision explainable, auditable, and safe.

## Track Alignment

Track 3 asks for an agent that can detect revenue at risk, choose the right intervention, execute a bounded recovery workflow, and show measured recovery across a batch.

This project focuses on payment-failure recovery:

- It reads failed payment records from `data/failed_payments.json`.
- It models each failed payment using Pydantic.
- It applies deterministic rules for common, high-confidence cases.
- It sends ambiguous cases to an LLM decision function.
- It validates the final decision before accepting it.
- It reports the action distribution and escalated cases.

## Architecture

The project follows a simple pipeline:

```text
failed payment data
        |
        v
FailedPayment model
        |
        v
rule-based classifier
        |
        +-- known case --> RecoveryDecision
        |
        +-- ambiguous case --> LLM decision
        |
        v
safety validator
        |
        v
batch recovery report
```

The main recovery path is implemented in:

```text
app/run_recovery.py
app/pipeline.py
app/classifier.py
app/llm.py
app/validator.py
app/models.py
```

## Project Structure

```text
recovery-agent/
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── classifier.py
│   ├── validator.py
│   ├── pipeline.py
│   ├── llm.py
│   ├── executor.py
│   ├── audit.py
│   └── run_recovery.py
├── data/
│   └── failed_payments.json
├── tests/
│   ├── test_classifier.py
│   ├── test_validator.py
│   ├── test_pipeline.py
│   └── run_batch.py
├── generate_failed_payments.py
├── requirements.txt
├── main.py
└── README.md
```

## Data Model

Each failed payment record contains:

```json
{
  "record_id": "fail_0001",
  "order_id": "order_100001",
  "merchant_id": "merch_grocerly",
  "customer_name": "Aarav Sharma",
  "customer_email": "aarav.sharma1@example.com",
  "customer_phone": "+919876543210",
  "amount": 1499.0,
  "payment_method": "card",
  "failure_reason": "insufficient_funds",
  "attempt_count": 1,
  "first_failed_at": "2026-08-20T10:30:00+00:00",
  "last_attempt_at": "2026-08-20T10:30:00+00:00",
  "is_subscription": false
}
```

The fields are represented in `app/models.py` using Pydantic models:

- `FailedPayment`: input payment failure record
- `RecoveryAction`: allowed recovery actions
- `RecoveryDecision`: final decision returned by the system

## Recovery Actions

The agent can choose one of four actions:

| Action | Meaning |
| --- | --- |
| `retry_now` | Retry after a very short delay for likely transient failures. |
| `retry_delayed` | Retry later, usually when the customer may need time to resolve the issue. |
| `send_payment_link` | Give the customer a fresh way to complete payment. |
| `escalate_to_human` | Stop automation and send the case for manual handling. |

## How Decisions Are Made

The classifier uses deterministic rules first. These rules are used when the failure reason has a clear recovery path.

Examples:

- `insufficient_funds` with one attempt -> `retry_delayed`
- `insufficient_funds` after multiple attempts -> `send_payment_link`
- `expired_card` -> `send_payment_link`
- `bank_timeout` -> `retry_now`
- `network_error` -> `retry_now`
- `invalid_otp` -> `retry_now`
- `attempt_count >= 3` -> `escalate_to_human`

Some failure reasons are intentionally treated as ambiguous:

- `issuer_declined`
- `gateway_error`

For these cases, `app/classifier.py` raises a `ValueError`. The pipeline catches that and calls `app/llm.py`, which asks an LLM to return a structured `RecoveryDecision`.

This split is deliberate. Rule-based logic is faster, cheaper, easier to test, and easier to explain. The LLM is reserved for cases where the failure reason needs more judgment.

## Safety Validation

The LLM decision is not trusted blindly. Every decision passes through `validate_decision()` in `app/validator.py`.

The validator enforces safety rules such as:

- If `attempt_count >= 3`, the final action must be `escalate_to_human`.
- `retry_now` can only have no delay or a short delay between 1 and 20 minutes.
- `retry_delayed` must have a delay between 30 minutes and 24 hours.
- `send_payment_link` and `escalate_to_human` must not include retry delays.

If a decision violates these constraints, the validator overrides it with a safe escalation.

## Setup

Create and activate a virtual environment:

```bash
python -m venv .venv
```

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

On macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file:

```text
NVIDIA_API_KEY=your_nvidia_api_key_here
```

The LLM client in `app/llm.py` uses NVIDIA's OpenAI-compatible endpoint:

```text
https://integrate.api.nvidia.com/v1
```

## Running The Project

Run the full recovery pipeline:

```bash
python -m app.run_recovery
```

Run tests:

```bash
pytest
```

Regenerate synthetic failed-payment data:

```bash
python generate_failed_payments.py
```

## Sample Output

Example output from `python -m app.run_recovery`:

```text
Loaded 56 payments

Recovery decisions:
  send_payment_link: 8
  escalate_to_human: 11
  retry_now: 17
  retry_delayed: 20

Processed: 56 payments

Escalated cases:
  fail_0002
  fail_0005
  fail_0009
  fail_0012
  fail_0014
  fail_0023
  fail_0024
  fail_0038
  fail_0043
  fail_0048
  fail_0053
```

## Testing

The test suite covers the core decision logic:

- `tests/test_classifier.py` checks deterministic recovery rules.
- `tests/test_validator.py` checks safety overrides.
- `tests/test_pipeline.py` checks that ambiguous failures can pass through the full pipeline.

Run all tests with:

```bash
pytest
```

Current local result:

```text
13 passed
```

## Design Decisions And Trade-Offs

- **Rules before LLM**: Most payment failures have predictable recovery behavior. Rules make those decisions fast, testable, and explainable.
- **LLM only for ambiguous failures**: The LLM is used for cases like issuer declines and gateway errors, where structured failure data may not be enough.
- **Bounded automation**: The system stops automatic recovery after three attempts. This prevents repeated retries from creating customer frustration or operational risk.
- **Validation after AI**: LLM output is treated as a recommendation, not final truth. The validator checks whether the decision is safe before accepting it.
- **Synthetic data first**: The repo uses generated payment data so the pipeline can be demonstrated without exposing real customer or merchant information.

## Current Scope

This repository currently demonstrates the decisioning and validation layer of a payment recovery workflow. It does not yet perform real Razorpay payment retries or create live Razorpay payment links. In a production Razorpay integration, this agent would sit behind payment failure webhooks and call Razorpay test-mode or live APIs depending on merchant configuration.

Expected production flow:

```text
Razorpay payment.failed webhook
        |
        v
recovery-agent receives failed payment
        |
        v
classifier or LLM chooses action
        |
        v
validator checks retry limits and safety rules
        |
        v
Razorpay API call / payment link / escalation queue
        |
        v
audit log and recovery report
```

## What I Would Build Next

- Add Razorpay test-mode Payment Link API integration for `send_payment_link`.
- Add persistent audit logging to write every decision to a JSON or SQLite audit store.
- Add recovery amount tracking so the report can show recovered revenue, unresolved amount, and recovery rate.
- Extend the same architecture to checkout abandonment, subscription failures, and overdue receivables.

## Submission Notes

The most important command for reviewers is:

```bash
python -m app.run_recovery
```

The most important test command is:

```bash
pytest
```

The project is intentionally small and explainable. The main engineering idea is that payment recovery should be automated where the decision is clear, AI-assisted where the case is ambiguous, and always bounded by safety rules.

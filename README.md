# recovery-agent

`recovery-agent` is a Python payment-recovery agent built for Razorpay's AI Builder Internship 2026, Track 3: AI Revenue Recovery. It takes failed payment records, decides the safest recovery action, executes supported recovery actions in test mode, and writes an audit trail for every decision. The project is intentionally small: the goal is to show a working, explainable recovery workflow rather than hide the core logic behind unnecessary abstractions.

## Problem

Failed payments are lost revenue unless they are handled quickly and safely. Some failures are temporary, such as network errors or bank timeouts. Others need a different customer action, such as an expired card or repeated insufficient funds. A recovery agent needs to decide what to do, avoid unsafe repeated retries, and explain every decision so a merchant or reviewer can audit the workflow.

## What It Does

- Loads synthetic failed payment records from `data/failed_payments.json`.
- Validates records with Pydantic models.
- Applies rule-based decisions for clear failure reasons.
- Uses an LLM for ambiguous reasons such as `issuer_declined` and `gateway_error`.
- Uses structured JSON output for LLM decisions.
- Validates every decision before accepting it.
- Creates Razorpay test-mode payment links for `send_payment_link` actions.
- Saves decision history to `data/audit_log.json`.
- Exposes a webhook endpoint for simulated Razorpay `payment.failed` events.
- Includes tests for classifier, validator, executor, pipeline, and webhook behavior.

## Architecture

```text
failed payment batch or webhook
        |
        v
FailedPayment model
        |
        v
rule-based classifier
        |
        +-- clear case --> RecoveryDecision
        |
        +-- ambiguous case --> LLM structured JSON decision
        |
        v
safety validator
        |
        v
executor / audit log / report
```

The same recovery pipeline is used by both the batch runner and the webhook endpoint.

## Project Structure

```text
recovery-agent/
├── app/
│   ├── __init__.py
│   ├── audit.py
│   ├── classifier.py
│   ├── executor.py
│   ├── llm.py
│   ├── models.py
│   ├── pipeline.py
│   ├── razorpay_client.py
│   ├── run_recovery.py
│   ├── validator.py
│   └── webhook.py
├── data/
│   ├── audit_log.json
│   └── failed_payments.json
├── tests/
│   ├── test_classifier.py
│   ├── test_executor.py
│   ├── test_pipeline.py
│   ├── test_razorpay_link.py
│   ├── test_validator.py
│   └── test_webhook.py
├── generate_failed_payments.py
├── main.py
├── requirements.txt
└── README.md
```

## Decision Logic

The classifier starts with deterministic rules because common payment failures usually have clear recovery behavior.

| Failure / condition | Action |
| --- | --- |
| `attempt_count >= 3` | `escalate_to_human` |
| `insufficient_funds`, first attempt | `retry_delayed` |
| `insufficient_funds`, multiple attempts | `send_payment_link` |
| `expired_card` | `send_payment_link` |
| `bank_timeout` | `retry_now` |
| `network_error` | `retry_now` |
| `invalid_otp` | `retry_now` |
| `issuer_declined` | LLM decision |
| `gateway_error` | LLM decision |

This split keeps predictable cases fast and explainable, while still allowing ambiguous gateway or issuer responses to be handled by an LLM.

## LLM Structured Output

`app/llm.py` uses NVIDIA's OpenAI-compatible endpoint:

```text
https://integrate.api.nvidia.com/v1
```

The LLM returns a structured `RecoveryDecision` object:

```json
{
  "record_id": "fail_0002",
  "action": "retry_now",
  "reasoning": "Issuer declined once, safe to retry.",
  "confidence": 0.85,
  "retry_delay_minutes": 5
}
```

An earlier version only asked the model to return JSON in the prompt. That was not reliable enough: the model sometimes returned long or incomplete reasoning text, which caused `json.loads()` to fail. The current version uses a JSON schema through `response_format`, keeps reasoning short, and still validates the decision in code after the model returns.

## Safety Validation

The LLM does not get final authority. `app/validator.py` enforces safety rules:

- `attempt_count >= 3` always escalates to a human.
- `retry_now` can use `null` or a delay between 1 and 20 minutes.
- `retry_delayed` must use a delay between 30 and 1440 minutes.
- `send_payment_link` and `escalate_to_human` cannot include retry delays.

If a decision violates these rules, the validator overrides it with `escalate_to_human`.

## Razorpay Integration

`app/razorpay_client.py` creates Razorpay test-mode payment links. `app/executor.py` calls this when the final action is `send_payment_link`.

Retries are currently simulated because real retry behavior depends on payment method, mandate status, and customer authorization. Payment Links are implemented because they are a clear, safe recovery action for cases like expired cards or repeated insufficient funds.

## Webhook Endpoint

`app/webhook.py` exposes a local FastAPI endpoint for simulated Razorpay failed-payment events:

```text
POST /webhooks/razorpay/payment-failed
```

This demonstrates how the agent would sit behind a Razorpay `payment.failed` webhook in a real integration.

## Setup

Create and activate a virtual environment:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create `.env`:

```text
NVIDIA_API_KEY=your_nvidia_api_key
RAZORPAY_KEY_ID=rzp_test_your_key_id
RAZORPAY_KEY_SECRET=your_test_key_secret
```

## Run

Run the batch recovery demo:

```bash
python -m app.run_recovery
```

or:

```bash
python main.py
```

Run the webhook server:

```bash
uvicorn app.webhook:app --reload
```

Run tests:

```bash
pytest
```

Generate synthetic data:

```bash
python generate_failed_payments.py
```

## Sample Batch Output

```text
Loaded 56 payments

Recovery decisions:
  send_payment_link: 4
  retry_now: 33
  retry_delayed: 16
  escalate_to_human: 3

Processed: 56 payments

Escalated cases:
  fail_0038
  fail_0043
  fail_0048
```

Audit entries are saved in `data/audit_log.json`.

## Tests

The test suite covers:

- rule-based classifier behavior
- validator safety overrides
- executor behavior with Razorpay payment-link creation mocked
- pipeline behavior with LLM and audit saving mocked
- webhook request handling

External API calls are mocked in automated tests. Manual smoke scripts are kept under `tests/` and guarded so they do not run during normal pytest collection.

Current local result:

```text
19 passed
```

## Design Decisions

- **Rules first**: deterministic logic is better for common payment failures because it is fast, cheap, and easy to audit.
- **LLM only for ambiguity**: the LLM is used for issuer and gateway responses where rigid rules may be too limited.
- **Validation after LLM**: structured output improves formatting, but business safety still belongs in code.
- **Payment Links before retries**: Razorpay test-mode Payment Links are safer and easier to demonstrate than real payment retry orchestration.
- **Audit trail by default**: every decision is recorded with source, action, reasoning, confidence, and validator override status.

## What I Would Build Next

- Add Razorpay webhook signature verification.
- Store audit logs in SQLite or Postgres instead of a JSON file.
- Track recovered amount after payment-link completion callbacks.
- Add a merchant-facing dashboard for recovery rate, unresolved amount, and failure-reason breakdown.

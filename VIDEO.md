# Demo Video Script

Use this as a 5-minute walkthrough script for the Razorpay AI Builder Internship submission.

## 0:00-0:30 - Opening

Say:

```text
This project is recovery-agent, built for Razorpay's AI Builder Internship 2026, Track 3: AI Revenue Recovery.
The problem is that failed payments are not always dead payments. Some can be recovered with the right retry, payment link, or escalation.
```

Show:

```text
README.md
```

## 0:30-1:00 - Data

Open:

```text
data/failed_payments.json
```

Say:

```text
This file contains synthetic failed payment records. Each record has merchant, customer, amount, payment method, failure reason, attempt count, and timestamps.
I used synthetic data so the demo does not depend on real customer information.
```

## 1:00-1:45 - Models And Rules

Open:

```text
app/models.py
app/classifier.py
```

Say:

```text
FailedPayment is the input model. RecoveryDecision is the output model.
The classifier handles clear cases with deterministic rules.
For example, expired cards get a payment link, bank timeouts get a retry, and three attempts always escalates to a human.
```

## 1:45-2:30 - LLM Fallback

Open:

```text
app/pipeline.py
app/llm.py
```

Say:

```text
Some cases are ambiguous, like issuer_declined and gateway_error.
For those, the classifier raises a ValueError and the pipeline calls the LLM.
The LLM returns a structured RecoveryDecision JSON object.
```

Mention the issue you faced:

```text
Initially, the LLM sometimes returned long or incomplete JSON. That broke json.loads because the response was not valid parseable JSON.
I fixed this by making the prompt ask for short reasoning and by using structured JSON schema output through response_format.
I still keep a validator after the LLM because structured output controls format, not business safety.
```

## 2:30-3:10 - Safety Validator

Open:

```text
app/validator.py
```

Say:

```text
The validator is the safety layer.
It prevents automatic recovery after three attempts.
It checks retry delay ranges.
It also prevents retry delays from appearing on payment-link or escalation decisions.
If the LLM gives an unsafe decision, the validator overrides it to human escalation.
```

## 3:10-3:50 - Razorpay And Webhook

Open:

```text
app/razorpay_client.py
app/executor.py
app/webhook.py
```

Say:

```text
For real Razorpay integration, I added Payment Link creation in test mode.
When the action is send_payment_link, the executor can call Razorpay's Payment Link API.
I also added a FastAPI webhook endpoint that simulates how Razorpay could send a payment.failed event into this agent.
```

Mention scope honestly:

```text
Retries are simulated for now because real retry orchestration depends on payment method, mandate state, and customer authorization.
Payment Links are implemented because they are a safe and demonstrable recovery action.
```

## 3:50-4:30 - Run Tests

Run:

```bash
pytest
```

Say:

```text
The tests cover classifier rules, validator safety overrides, executor behavior, pipeline behavior, and webhook handling.
External calls are mocked in tests so the test suite stays reliable.
```

## 4:30-5:00 - Run Project

Run:

```bash
python -m app.run_recovery
```

Show:

```text
data/audit_log.json
```

Say:

```text
The batch runner processes all failed payments, prints the action breakdown, and writes an audit log.
The audit log records the action, source, reasoning, confidence, retry delay, and whether the validator overrode the decision.
```

## Closing

Say:

```text
The main design choice is simple: use deterministic rules where the recovery decision is obvious, use the LLM only for ambiguous cases, and always validate the decision before taking action.
Next I would add Razorpay webhook signature verification and track actual recovered amount after payment-link completion.
```

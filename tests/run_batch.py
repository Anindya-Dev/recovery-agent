import json
from pathlib import Path
from collections import Counter

from app.classifier import decide
from app.models import FailedPayment

data_path = Path(__file__).parent.parent / "data" / "failed_payments.json"

with open(data_path, "r") as file:
    payments_data = json.load(file)

payments = [FailedPayment(**payment) for payment in payments_data]

decisions = []
errors = []

for payment in payments:
    try:
        decision = decide(payment)
        decisions.append(decision)
    except ValueError as e:
        errors.append((payment, str(e)))

action_counts = Counter(decision.action.value for decision in decisions)

print("\nRecovery decisions:")
for action, count in action_counts.items():
    print(f"  {action}: {count}")

print(f"\nAwaiting LLM: {len(errors)}")

print("\nCases awaiting LLM:")
for payment, error in errors:
    print(
        f"  {payment.record_id} | "
        f"{payment.failure_reason} | "
        f"attempts={payment.attempt_count} | "
        f"amount={payment.amount}"
    )

print("\nEscalated cases:")
for decision in decisions:
    if decision.action.value == "escalate_to_human":
        print(f"  {decision.record_id}")
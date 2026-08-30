import json
from pathlib import Path
from collections import Counter

from .models import FailedPayment
from .pipeline import recover_payment


def load_payments() -> list[FailedPayment]:
    data_path = Path(__file__).parent.parent / "data" / "failed_payments.json"

    with open(data_path, "r", encoding="utf-8") as file:
        payments_data = json.load(file)

    return [
        FailedPayment(**payment)
        for payment in payments_data
    ]


def main():
    payments = load_payments()

    print(f"Loaded {len(payments)} payments")

    decisions = []

    for payment in payments:
        decision = recover_payment(payment)
        decisions.append(decision)

    action_counts = Counter(
        decision.action.value
        for decision in decisions
    )

    print("\nRecovery decisions:")

    for action, count in action_counts.items():
        print(f"  {action}: {count}")

    print(f"\nProcessed: {len(decisions)} payments")

    print("\nEscalated cases:")

    for decision in decisions:
        if decision.action.value == "escalate_to_human":
            print(f"  {decision.record_id}")


if __name__ == "__main__":
    main()
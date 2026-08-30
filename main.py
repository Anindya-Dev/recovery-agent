import json
from pathlib import Path

from app.audit import build_audit_entry
from app.classifier import classify_failure
from app.executor import decide_action
from app.validator import validate_record


DATA_FILE = Path("data/failed_payments.json")


def main():
    records = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    audit_entries = []

    for record in records:
        validate_record(record)
        record["failure_reason"] = classify_failure(record)
        action = decide_action(record)
        audit_entries.append(build_audit_entry(record, action))

    total_amount = sum(entry["amount"] for entry in audit_entries)

    print(f"Processed {len(audit_entries)} failed payments")
    print(f"Total amount at stake: INR {total_amount:,}")


if __name__ == "__main__":
    main()

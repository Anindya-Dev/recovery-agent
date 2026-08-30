from .models import FailedPayment, RecoveryDecision
from .classifier import decide
from .llm import llm_decide
from .validator import validate_decision

def recover_payment(payment: FailedPayment)-> RecoveryDecision:
    try:
        decision = decide(payment)
    except ValueError:
        decision= llm_decide(payment)
    decision= validate_decision(payment,decision)

    return decision
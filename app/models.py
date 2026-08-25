from enum import Enum
from pydantic import BaseModel,Field
from typing import Optional

class RecoveryAction(str,Enum):
    RETRY_NOW="retry_now"
    RETRY_DELAYED="retry_delayed"
    SEND_PAYMENT_LINK="send_payment_link"
    ESCALATE_TO_HUMAN="escalate_to_human"

class RecoveryDecision(BaseModel):
    record_id:str
    action:RecoveryAction
    reasoning:str
    confidence: float= Field(ge=0.0, le=1.0)
    retry_delay_minutes: Optional[int]=None


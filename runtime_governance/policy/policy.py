from enum import Enum
from dataclasses import dataclass

class Decision(str, Enum):
    ALLOW = "allow"
    ESCALATE = "escalate"
    BLOCK = "block"

@dataclass(frozen=True)
class PolicyDecision:
    decision: Decision
    reason: str

class PolicyEngine:
    def __init__(self, block_th=0.85, escalate_th=0.6):
        self.block_th = block_th
        self.escalate_th = escalate_th

    def decide(self, max_risk: float, ema_risk: float) -> PolicyDecision:
        if max_risk >= self.block_th:
            return PolicyDecision(Decision.BLOCK, "High-risk injection detected")

        if ema_risk >= self.escalate_th:
            return PolicyDecision(Decision.ESCALATE, "Sustained elevated risk")

        return PolicyDecision(Decision.ALLOW, "Risk below threshold")

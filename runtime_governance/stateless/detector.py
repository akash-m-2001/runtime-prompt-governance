import time
from dataclasses import dataclass

@dataclass(frozen=True)
class DetectionResult:
    p_injection: float
    latency_ms: float

class StatelessDetector:
    """
    Adapter for RoBERTa prompt-injection model.
    Replace `predict_proba` internals with your trained model.
    """

    def predict_proba(self, text: str) -> DetectionResult:
        start = time.perf_counter()

        # ---- REPLACE THIS BLOCK WITH REAL INFERENCE ----
        lowered = text.lower()
        triggers = ["ignore previous instructions", "system prompt", "developer"]
        p = 0.9 if any(t in lowered for t in triggers) else 0.05
        # ------------------------------------------------

        latency = (time.perf_counter() - start) * 1000
        return DetectionResult(p_injection=p, latency_ms=latency)

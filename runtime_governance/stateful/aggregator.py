from dataclasses import dataclass, field
import time

@dataclass
class SessionState:
    session_id: str
    ema_risk: float = 0.0
    max_risk: float = 0.0
    turns: int = 0
    last_updated: float = field(default_factory=time.time)

class StatefulAggregator:
    def __init__(self, alpha: float = 0.3):
        self.alpha = alpha
        self.sessions = {}

    def update(self, session_id: str, p_injection: float) -> SessionState:
        state = self.sessions.get(session_id, SessionState(session_id))
        state.turns += 1
        state.max_risk = max(state.max_risk, p_injection)
        state.ema_risk = self.alpha * p_injection + (1 - self.alpha) * state.ema_risk
        state.last_updated = time.time()
        self.sessions[session_id] = state
        return state

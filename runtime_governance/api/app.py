from fastapi import FastAPI
from pydantic import BaseModel

from stateless.detector import StatelessDetector
from stateful.aggregator import StatefulAggregator
from policy.policy import PolicyEngine

app = FastAPI()

detector = StatelessDetector()
aggregator = StatefulAggregator()
policy = PolicyEngine()


class PromptRequest(BaseModel):
    session_id: str
    prompt: str


@app.post("/check_prompt")
def check_prompt(req: PromptRequest):

    det = detector.predict_proba(req.prompt)

    state = aggregator.update(req.session_id, det.p_injection)

    decision = policy.decide(
        max_risk=state.max_risk,
        ema_risk=state.ema_risk
    )

    return {
        "decision": decision.decision,
        "risk": det.p_injection
    }
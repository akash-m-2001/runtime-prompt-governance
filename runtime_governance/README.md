# Runtime Prompt Governance

A system for detecting prompt injection attacks in LLM applications.

Features:
- Prompt classification using RoBERTa
- Session-level risk aggregation
- Policy-based guardrails
- FastAPI service for runtime detection

Tech Stack:
Python, HuggingFace Transformers, FastAPI, Docker


## Runtime Governance Evaluation

We evaluated a prompt-injection governance system on a balanced dataset
(200 benign, 200 injection prompts).

### Stateless baseline
- False allow rate: 0.98
- False block rate: 0.00

Single-shot detection fails to prevent most attacks when tuned to avoid
false positives.

### Stateful governance
- False allow rate: 0.04
- False block rate: 0.00

Aggregating risk across prompts reduces attack success by 25× without
blocking benign traffic.

### Key insight
Temporal aggregation and policy logic are more important than improving
single-prompt classification accuracy for real-world LLM safety.


pip install -r requirements.txt
uvicorn api.main:app

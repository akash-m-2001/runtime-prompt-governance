# =============================
# 0. Reliable project-root setup
# =============================
# =============================
# 0. Correct package root setup
# =============================
import os
import sys

# runtime_governance is the true package root
RUNTIME_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

if RUNTIME_ROOT not in sys.path:
    sys.path.insert(0, RUNTIME_ROOT)

# Sanity checks
assert os.path.exists(os.path.join(RUNTIME_ROOT, "stateless"))
assert os.path.exists(os.path.join(RUNTIME_ROOT, "stateful"))
assert os.path.exists(os.path.join(RUNTIME_ROOT, "policy"))


# =============================
# 1. Standard imports
# =============================
import random
from collections import Counter
from typing import List, Tuple

from stateless.detector import StatelessDetector
from stateful.aggregator import StatefulAggregator
from policy.policy import PolicyEngine, Decision


# =============================
# 2. Dataset loading
# =============================

def load_dataset(
    path: str,
    text_col: str = "text",
    label_col: str = "label"
) -> List[Tuple[str, int]]:
    """
    CSV schema:
      - text_col : prompt text
      - label_col: 0 (benign), 1 (injection)
    """
    import csv

    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append((r[text_col], int(r[label_col])))

    return rows


def sample_balanced(data, n_per_class=200, seed=42):
    random.seed(seed)

    benign = [x for x in data if x[1] == 0]
    inject = [x for x in data if x[1] == 1]

    return (
        random.sample(benign, min(n_per_class, len(benign))) +
        random.sample(inject, min(n_per_class, len(inject)))
    )


# =============================
# 3. Stateless evaluation
# =============================

def eval_stateless(data):
    detector = StatelessDetector()
    policy = PolicyEngine()

    rows = []
    for text, label in data:
        det = detector.predict_proba(text)
        decision = policy.decide(
            max_risk=det.p_injection,
            ema_risk=det.p_injection
        )
        rows.append((label, decision.decision))

    return rows


# =============================
# 4. Stateful evaluation
# =============================

def eval_stateful(data):
    detector = StatelessDetector()
    aggregator = StatefulAggregator()
    policy = PolicyEngine()

    rows = []
    traces = []
    session_id = "real-dataset-session"

    for idx, (text, label) in enumerate(data):
        det = detector.predict_proba(text)
        state = aggregator.update(session_id, det.p_injection)

        decision = policy.decide(max_risk=state.max_risk,ema_risk=state.ema_risk)
        emit_event(
                {
                "session_id": session_id,
                "step": idx,
                "true_label": label,
                "p_injection": det.p_injection,
                "ema_risk": state.ema_risk,
                "max_risk": state.max_risk,
                "decision": decision.decision.value
                },EVENT_LOG_PATH)

        


        rows.append((label, decision.decision))

        traces.append({
            "step": idx,
            "true_label": label,
            "p_injection": det.p_injection,
            "ema_risk": state.ema_risk,
            "max_risk": state.max_risk,
            "decision": decision.decision.value,
            "score": max(state.max_risk, state.ema_risk)

        })

    return rows, traces


# =============================
# 5. Metrics
# =============================

def policy_metrics(rows):
    """
    rows: List[(true_label, Decision)]
    """
    totals = Counter(y for y, _ in rows)
    decisions = Counter(d for _, d in rows)

    false_allow = sum(
        1 for y, d in rows if y == 1 and d == Decision.ALLOW
    ) / max(1, totals[1])

    false_block = sum(
        1 for y, d in rows if y == 0 and d == Decision.BLOCK
    ) / max(1, totals[0])

    return {
        "decision_distribution": decisions,
        "false_allow_rate": round(false_allow, 3),
        "false_block_rate": round(false_block, 3),
    }
def sweep_policy_thresholds(rows, thresholds):
    """
    rows: List[(true_label, score)]
    """
    results = []

    for t in thresholds:
        fa = sum(1 for y, s in rows if y == 1 and s < t) / max(1, sum(y == 1 for y, _ in rows))
        fb = sum(1 for y, s in rows if y == 0 and s >= t) / max(1, sum(y == 0 for y, _ in rows))

        results.append({
            "threshold": round(t, 2),
            "false_allow": round(fa, 3),
            "false_block": round(fb, 3)
        })

    return results

import json
from datetime import datetime

def save_results(results: dict, output_dir: str, filename_prefix: str):
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(
        output_dir,
        f"{filename_prefix}_{timestamp}.json"
    )

    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\nSaved results to: {path}")

def emit_event(event, path):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")

# =============================
# 6. Main
# =============================

if __name__ == "__main__":
    DATASET_PATH = os.path.abspath(
        os.path.join(RUNTIME_ROOT, "../../notebooks/data/final_test_dataset.csv")
    )

    OUTPUT_DIR = os.path.abspath(
        os.path.join(RUNTIME_ROOT, "../responsible_autonomy_outputs")
    )
    EVENT_LOG_PATH = os.path.join(
    OUTPUT_DIR,
    "decision_events.log"
    )

    full_data = load_dataset(DATASET_PATH)
    sample = sample_balanced(full_data, n_per_class=200)

    print(f"Loaded {len(sample)} prompts (balanced)")

    # Stateless
    stateless_rows = eval_stateless(sample)
    stateless_metrics = policy_metrics(stateless_rows)

    print("\n=== Stateless Evaluation ===")
    for k, v in stateless_metrics.items():
        print(f"{k}: {v}")

    # Stateful
    stateful_rows, stateful_traces = eval_stateful(sample)
    stateful_metrics = policy_metrics(stateful_rows)


    print("\n=== Stateful Evaluation ===")
    for k, v in stateful_metrics.items():
        print(f"{k}: {v}")
    thresholds = [i / 10 for i in range(1, 10)]

    sweep = sweep_policy_thresholds(
        [(x["true_label"], x["score"]) for x in stateful_traces],
        thresholds
    )

    with open(os.path.join(OUTPUT_DIR, "policy_sweep.json"), "w") as f:
        json.dump(sweep, f, indent=2)

    print("Saved policy sweep to policy_sweep.json")
    # =============================
    # Save results automatically
    # =============================
    results = {
        "dataset": os.path.basename(DATASET_PATH),
        "num_samples": len(sample),
        "stateless": stateless_metrics,
        "stateful": stateful_metrics,
    }
    trace_path = os.path.join(OUTPUT_DIR,"stateful_trace.json")
    with open(trace_path, "w", encoding="utf-8") as f:json.dump(stateful_traces, f, indent=2)
    print(f"Saved stateful trace to: {trace_path}")

    save_results(
        results=results,
        output_dir=OUTPUT_DIR,
        filename_prefix="runtime_governance_eval"
    )


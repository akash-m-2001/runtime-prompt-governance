import json
import matplotlib.pyplot as plt
import os

TRACE_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "../../responsible_autonomy_outputs/stateful_trace.json"
    )
)

with open(TRACE_PATH, "r") as f:
    trace = json.load(f)

steps = [x["step"] for x in trace]
ema_risk = [x["ema_risk"] for x in trace]
inst_risk = [x["p_injection"] for x in trace]
decisions = [x["decision"] for x in trace]

plt.figure(figsize=(10, 5))

plt.plot(steps, ema_risk, label="EMA Risk (Stateful)", linewidth=2)
plt.plot(steps, inst_risk, label="Instant Risk (Stateless)", alpha=0.4)

# Mark block decisions
for x in trace:
    if x["decision"] == "block":
        plt.axvline(x["step"], color="red", alpha=0.05)

plt.xlabel("Prompt index")
plt.ylabel("Risk score")
plt.title("Stateful Risk Accumulation vs Stateless Risk")
plt.legend()
plt.tight_layout()

# Save the figure
OUTPUT_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "../../responsible_autonomy_outputs/risk_accumulation.png"
    )
)

plt.savefig(OUTPUT_PATH)
plt.show()

print(f"Saved plot to: {OUTPUT_PATH}")

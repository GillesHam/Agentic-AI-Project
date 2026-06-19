"""
EXECUTE tools, deterministic computations the agent invokes for prediction and
scoring (addresses: "No real-time ETA predictions" and unprioritized risk).

These are intentionally simple, transparent heuristics. In production they would
be the fine-tuned / ML models discussed in Session 7 (RUL, ETA, anomaly). Keeping
them as glass-box functions makes the MVP fully reproducible offline.
"""

from datetime import date, datetime, timedelta
from . import Tool, register
from ._data import load


def _parse(d):
    return datetime.fromisoformat(d.replace("Z", "")).date() if "T" in d else date.fromisoformat(d)


# ---------------------------------------------------------------------------
# ETA predictor, combines promised ETA + carrier status + active disruptions
# ---------------------------------------------------------------------------
def _eta_predictor(shipment_id):
    sh = load("shipments")
    events = load("external_events")["events"]
    row = next((s for s in sh["shipments"] if s["shipment_id"] == shipment_id), None)
    if not row:
        return {"error": f"unknown shipment {shipment_id}"}

    promised = _parse(row["promised_eta"])
    delay = 0
    reasons = []

    status_penalty = {
        "AT_PORT_NOT_LOADED": 5,
        "AWAITING_COMPONENTS_AT_SUPPLIER": 9,
        "IN_TRANSIT": 0,
    }
    p = status_penalty.get(row["last_known_status"], 2)
    if p:
        delay += p
        reasons.append(f"status '{row['last_known_status']}' adds ~{p}d")

    # disruption signals tied to this shipment's origin/supplier
    for e in events:
        hit = (e.get("location") == row.get("origin")) or (e.get("entity") == row.get("supplier"))
        if hit and e["severity"] in ("high", "medium"):
            add = 7 if e["severity"] == "high" else 3
            delay += add
            reasons.append(f"event {e['event_id']} ({e['severity']}) adds ~{add}d")

    predicted = promised + timedelta(days=delay)
    return {
        "shipment_id": shipment_id,
        "promised_eta": str(promised),
        "predicted_eta": str(predicted),
        "predicted_delay_days": delay,
        "confidence": "medium" if delay else "high",
        "explanation": reasons or ["no active risk signals; tracking to plan"],
    }


register(Tool(
    name="eta_predictor",
    description=(
        "Predict a realistic ETA for an in-transit shipment by combining its promised "
        "ETA, last-known carrier status and any active external disruption signals. "
        "Returns predicted_eta, delay in days, confidence and a human-readable "
        "explanation. Use this to replace static promised dates with a real-time ETA."
    ),
    action_type="execute",
    requires_approval=False,
    permissions="stateless compute; no system writes",
    fn=_eta_predictor))


# ---------------------------------------------------------------------------
# Risk scorer, turns signals into a prioritized 0-100 score (no auto-action)
# ---------------------------------------------------------------------------
def _risk_scorer(part, runway_days, predicted_delay_days, single_source, line_stoppage_cost_per_day):
    # exposure window: how many days the line would be starved
    exposure = max(0, predicted_delay_days - runway_days)
    score = 0
    score += min(40, exposure * 6)                       # time pressure
    score += 20 if single_source else 0                  # no fallback
    score += min(25, int(line_stoppage_cost_per_day / 8000))  # financial impact
    score += 15 if runway_days < 7 else 0                # thin buffer
    score = min(100, score)
    band = "LOW"
    if score >= 70:
        band = "CRITICAL"
    elif score >= 45:
        band = "HIGH"
    elif score >= 25:
        band = "MEDIUM"
    return {
        "part": part,
        "risk_score": score,
        "risk_band": band,
        "exposure_days": exposure,
        "estimated_exposure_cost": exposure * line_stoppage_cost_per_day,
        "rationale": (
            f"exposure={exposure}d, single_source={single_source}, "
            f"runway={runway_days}d, stoppage_cost/day=${line_stoppage_cost_per_day:,}"
        ),
    }


register(Tool(
    name="risk_scorer",
    description=(
        "Compute a 0-100 supply-risk score and band (LOW/MEDIUM/HIGH/CRITICAL) for a "
        "part from inventory runway, predicted delay, single-source status and "
        "line-stoppage cost. Returns the exposure window in days and estimated "
        "exposure cost. Use this to PRIORITIZE which risks deserve action."
    ),
    action_type="execute",
    requires_approval=False,
    permissions="stateless compute; no system writes",
    fn=_risk_scorer))

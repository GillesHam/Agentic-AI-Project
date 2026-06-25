"""
sentinel_runtime.py, the bridge between the Supply Chain Sentinel agent code (in src/)
and any UI. It runs the real Orchestrator + sub-agents, captures the structured trace
via tracer.SINK, and derives the dashboard metrics and the supplier-graph diagram.

This module deliberately imports NO streamlit, so it can be unit-tested headlessly:
    python -c "import sentinel_runtime as r; print(len(r.run_sentinel()['events']))"
"""

import os
import sys

# --- make `import tracer / tools / llm / agents / orchestrator` resolve from src/ ---
_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import tracer                       # noqa: E402
import tools                        # noqa: E402  (registry)
import tools.data_access            # noqa: E402,F401  (registers read tools)
import tools.analytics              # noqa: E402,F401  (registers execute tools)
import tools.actions                # noqa: E402,F401  (registers write tools)
import tools._data as _dm           # noqa: E402  (loader + scenario overrides)
import llm                          # noqa: E402
from tools._data import load        # noqa: E402
from orchestrator import Orchestrator, OBJECTIVE  # noqa: E402
from agents.risk_intel_agent import RiskIntelAgent          # noqa: E402
from agents.supplier_graph_agent import SupplierGraphAgent  # noqa: E402
from agents.eta_logistics_agent import ETALogisticsAgent    # noqa: E402
from agents.mitigation_agent import (                        # noqa: E402
    MitigationAgent, LINE_STOPPAGE_COST_PER_DAY, UNIT_COST, ALT_PREMIUM_PCT)

DEFAULT_TRIGGER = (
    "Scheduled 15-min control-tower scan + external_risk_feed webhook "
    "(EVT-7001 typhoon @ Kaohsiung, EVT-7002 SiliconPath fab halt)"
)

# =====================================================================================
# Scenarios. Each is a small transform over the base JSON fixtures (events + inventory),
# so the SAME agents react differently. They demonstrate distinct agentic behaviours:
# full mitigation, restraint when irrelevant, and standing down when there is no risk.
# =====================================================================================
PART = "SVC-2200"


def _set_sev(events, overrides):
    for e in events["events"]:
        if e["event_id"] in overrides:
            e["severity"] = overrides[e["event_id"]]
    return events


def _set_inv(inv, part, **fields):
    inv["items"][part].update(fields)
    return inv


SCENARIOS = {
    "taiwan": {
        "emoji": "🌀", "label": "Taiwan chip shock",
        "blurb": "A typhoon shuts Kaohsiung port and a grid fault halts the SiliconPath "
                 "chip fab. No Tier-1 order looks late yet.",
        "expected": "CRITICAL, switches to a safe alternate, asks a human to approve.",
        "trigger": DEFAULT_TRIGGER,
        "events": lambda e: e,
        "inventory": lambda i: i,
    },
    "lowstock": {
        "emoji": "🔥", "label": "Same shock, almost no stock",
        "blurb": "The same Taiwan disruption, but we are down to a fraction of a day of "
                 "buffer stock on the critical controller.",
        "expected": "CRITICAL with a much larger amount of money at risk.",
        "trigger": "Risk webhook (Taiwan) + ERP low-stock alert on " + PART,
        "events": lambda e: e,
        "inventory": lambda i: _set_inv(i, PART, on_hand_units=312),  # runway ~0.2 days
    },
    "portstrike": {
        "emoji": "⚓", "label": "Distant port strike",
        "blurb": "A labour strike halts the Port of Los Angeles. The Taiwan signals are "
                 "quiet. Does it affect any of our critical parts?",
        "expected": "Perceived, but it touches no critical part, so no action.",
        "trigger": "External risk webhook (EVT-8001 Port of Los Angeles strike)",
        "events": lambda e: _add_la_strike(_set_sev(e, {"EVT-7001": "low", "EVT-7002": "low"})),
        "inventory": lambda i: i,
    },
    "allclear": {
        "emoji": "✅", "label": "Calm seas",
        "blurb": "A routine scan with only minor, low-severity chatter in the feed.",
        "expected": "No high-severity risk, the agent stands down. No false alarm.",
        "trigger": "Scheduled 15-min control-tower scan (no high-severity signals)",
        "events": lambda e: _set_sev(e, {"EVT-7001": "low", "EVT-7002": "low"}),
        "inventory": lambda i: i,
    },
}
SCENARIO_ORDER = ["taiwan", "lowstock", "portstrike", "allclear"]


def _add_la_strike(events):
    events["events"].append({
        "event_id": "EVT-8001", "type": "logistics", "severity": "high",
        "headline": "Labour strike halts container operations at the Port of Los Angeles",
        "location": "PORT-LOSANGELES", "region": "NA",
        "published": "2026-06-18T07:30:00Z",
    })
    return events


def _scenario_overrides(scenario_key, inv_tweaks=None):
    """Build the {dataset_name: data} overrides for a scenario (+ optional UI tweaks)."""
    sc = SCENARIOS[scenario_key]
    events = sc["events"](_dm.read_file("external_events"))
    inv = sc["inventory"](_dm.read_file("inventory"))
    if inv_tweaks:
        _set_inv(inv, PART, **{k: v for k, v in inv_tweaks.items() if v is not None})
    return {"external_events": events, "inventory": inv}

AGENT_CLASSES = [Orchestrator, RiskIntelAgent, SupplierGraphAgent,
                 ETALogisticsAgent, MitigationAgent]

# agent_start "name" -> a short, friendly label for the pipeline view
AGENT_LABELS = {
    "RiskIntelAgent": "Risk Intel",
    "SupplierGraphAgent": "Supplier Graph",
    "ETALogisticsAgent": "ETA & Logistics",
    "MitigationAgent": "Mitigation",
}
AGENT_ORDER = ["RiskIntelAgent", "SupplierGraphAgent", "ETALogisticsAgent", "MitigationAgent"]


def run_sentinel(scenario="taiwan", backend="sim", model="claude-opus-4-8",
                 inv_tweaks=None, trigger=None):
    """Run the full agentic pipeline once for a scenario and capture everything for the UI.

    Returns a dict: events (structured trace), scenario, objective, trigger, plan,
    approvals, briefings, metrics, affected, impacted, chosen_alt, conclusion, backend.
    """
    sc = SCENARIOS.get(scenario, SCENARIOS["taiwan"])
    trigger = trigger or sc["trigger"]

    # configure the reasoning backend (llm.BACKEND is read live by draft_briefing)
    llm.BACKEND = backend
    llm.MODEL = model

    events = []
    tracer.SINK = events
    tracer.SLOW = False  # the UI does its own pacing on replay
    _dm.set_overrides(_scenario_overrides(scenario, inv_tweaks))
    try:
        orch = Orchestrator()
        orch.run(trigger)
        briefings = [llm.draft_briefing(c) for c in orch.briefing_contexts()]
        metrics = _derive_metrics(orch.board)
    finally:
        tracer.SINK = None       # never leave the global sink attached
        _dm.clear_overrides()    # restore the on-disk fixtures

    board = orch.board
    affected = board.recall("affected_entities", [])
    impacted = board.recall("impacted_parts", [])

    return {
        "events": events,
        "scenario": scenario,
        "inv_tweaks": inv_tweaks,
        "objective": OBJECTIVE,
        "trigger": trigger,
        "plan": list(board.plan),
        "approvals": list(board.approvals_required),
        "briefings": briefings,
        "metrics": metrics,
        "affected": affected,
        "impacted": impacted,
        "chosen_alt": metrics.get("chosen_alt"),
        "conclusion": _conclusion(affected, impacted, board.plan),
        "backend": backend,
    }


def _conclusion(affected, impacted, plan):
    """Classify how the run ended, so the UI can explain the agent's judgement."""
    if not affected:
        return "no_risk"          # nothing high-severity, stood down
    if not impacted:
        return "not_relevant"     # perceived a disruption but it hits no critical part
    if not plan:
        return "monitor"          # impacted but risk acceptable, monitor only
    return "mitigated"            # full mitigation plan produced


def _derive_metrics(board):
    """Re-derive the headline numbers from the same tools the agents used, so the
    KPI cards are authentic rather than hand-typed."""
    impacted = board.recall("impacted_parts", [])
    eta = board.recall("eta_findings", {})
    affected = set(board.recall("affected_entities", []))
    if not impacted:
        return {}
    item = impacted[0]
    part = item["part"]

    inv = tools.get("inventory_system")(part=part)
    runway = inv["runway_days_to_safety_stock"]
    delay = eta[part]["predicted_delay_days"]
    score = tools.get("risk_scorer")(
        part=part, runway_days=runway, predicted_delay_days=delay,
        single_source=item["single_source_upstream"],
        line_stoppage_cost_per_day=LINE_STOPPAGE_COST_PER_DAY)

    chosen_alt = _alternate_avoiding_disruption(item, affected)
    qty = 600
    unit = round(UNIT_COST.get(part, 500) * (1 + ALT_PREMIUM_PCT / 100), 2)

    return {
        "part": part,
        "part_name": item["name"],
        "risk_band": score["risk_band"],
        "risk_score": score["risk_score"],
        "exposure_days": score["exposure_days"],
        "exposure_cost": score["estimated_exposure_cost"],
        "runway_days": runway,
        "delay_days": delay,
        "predicted_eta": eta[part]["predicted_eta"],
        "single_source": item["single_source_upstream"],
        "chosen_alt": chosen_alt,
        "chosen_alt_name": load("suppliers")["suppliers"].get(chosen_alt, {}).get("name", chosen_alt),
        "po_qty": qty,
        "po_unit_cost": unit,
        "po_spend": round(qty * unit, 2),
        "line_stoppage_cost_per_day": LINE_STOPPAGE_COST_PER_DAY,
    }


# --- supplier graph helpers (shared with MitigationAgent's logic) -------------------
def _chain_ids(data, sid, seen=None):
    seen = seen or set()
    if sid in seen:
        return []
    seen.add(sid)
    out = [sid]
    for dep in data["suppliers"].get(sid, {}).get("depends_on", []):
        out += _chain_ids(data, dep, seen)
    return out


def _alternate_avoiding_disruption(item, affected):
    data = load("suppliers")
    for sid in item["qualified_suppliers"]:
        if not (set(_chain_ids(data, sid)) & set(affected)):
            return sid
    return item["qualified_suppliers"][-1]


def build_graph_dot(affected=None, chosen_alt=None, impacted_parts=None):
    """Build a Graphviz DOT string of the multi-tier supplier graph.

    Disrupted entities are red, the chosen alternate is green, impacted parts amber.
    Pass empty/None args to render the neutral (pre-run) graph.
    """
    affected = set(affected or [])
    impacted_parts = set(impacted_parts or [])
    data = load("suppliers")
    parts = data["parts"]
    suppliers = data["suppliers"]

    lines = [
        "digraph supply {",
        "  rankdir=LR;",
        '  bgcolor="transparent";',
        '  node [fontname="Helvetica" fontsize=10 style="filled" color="#cbd5e1"];',
        '  edge [color="#94a3b8" fontname="Helvetica" fontsize=8];',
    ]

    for pid, p in parts.items():
        fill = "#fde68a" if pid in impacted_parts else "#e2e8f0"
        lines.append(
            f'  "{pid}" [shape=box label="{pid}\\n{p["name"]}" fillcolor="{fill}"];')

    for sid, s in suppliers.items():
        if sid in affected:
            fill = "#fca5a5"          # disrupted -> red
        elif sid == chosen_alt:
            fill = "#86efac"          # chosen mitigation route -> green
        else:
            fill = "#f1f5f9"
        tier = s.get("tier", "?")
        lines.append(
            f'  "{sid}" [shape=ellipse label="{s["name"]}\\nTier {tier} | {s.get("country","")}" '
            f'fillcolor="{fill}"];')

    for pid, p in parts.items():
        for sid in p.get("qualified_suppliers", []):
            label = "alternate" if sid == chosen_alt else "supplies"
            lines.append(f'  "{sid}" -> "{pid}" [label="{label}"];')
    for sid, s in suppliers.items():
        for dep in s.get("depends_on", []):
            lines.append(f'  "{dep}" -> "{sid}";')

    lines.append("}")
    return "\n".join(lines)


def agent_prompts():
    """Return [(name, system_prompt)] for every agent (the graded deliverable)."""
    return [(a.name, a.system_prompt) for a in AGENT_CLASSES]


def tool_catalog():
    """Return [(name, action_type, requires_approval, permissions, description)]."""
    return [(t.name, t.action_type, t.requires_approval, t.permissions, t.description)
            for t in tools.all_tools()]

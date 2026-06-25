"""
Supply Chain Sentinel, interactive demo dashboard (Streamlit).

This drives the REAL multi-agent system (src/orchestrator.py + the four sub-agents)
and replays exactly what they did, step by step, with live human-in-the-loop approval.

Run from the mvp/ folder:
    pip install -r app_requirements.txt
    streamlit run streamlit_app.py

Runs fully offline and deterministically, no API key needed.
"""

import time
import streamlit as st
import sentinel_runtime as rt

st.set_page_config(page_title="Supply Chain Sentinel", page_icon="🛡️", layout="wide")

# --- phase / event styling ---------------------------------------------------------
PHASE_COLOR = {
    "PERCEIVE": "#0891b2", "REASON": "#7c3aed", "PLAN": "#2563eb",
    "ACT": "#d97706", "OBSERVE": "#16a34a", "ADAPT": "#dc2626",
    "HITL": "#ca8a04", "AGENT": "#0e7c86",
}
NAVY = "#0a1f6b"


def chip(text, color, fg="#ffffff"):
    return (f"<span style='background:{color};color:{fg};padding:2px 8px;border-radius:6px;"
            f"font-size:0.72rem;font-weight:700;letter-spacing:.3px'>{text}</span>")


# --- session state -----------------------------------------------------------------
def _init():
    st.session_state.setdefault("run", None)
    st.session_state.setdefault("cursor", 0)
    st.session_state.setdefault("halted", False)
    st.session_state.setdefault("auto", False)


_init()


def start_run(scenario, inv_tweaks=None):
    with st.spinner("Running the agentic pipeline..."):
        st.session_state.run = rt.run_sentinel(scenario=scenario, inv_tweaks=inv_tweaks)
    st.session_state.cursor = 0
    st.session_state.halted = False
    st.session_state.auto = False


def reset_run():
    st.session_state.run = None
    st.session_state.cursor = 0
    st.session_state.halted = False
    st.session_state.auto = False


# --- sidebar -----------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🛡️ Supply Chain Sentinel")
    st.caption("Agentic AI for IT, IE University. An always-on AI teammate that protects "
               "Titan's production lines from supply shocks.")

    speed = st.slider("Auto-play speed (seconds per step)", 0.1, 2.0, 0.5, 0.1)

    st.divider()
    st.markdown("### Tweak the situation")
    st.caption("Change our stock position, then run the Taiwan shock to watch the risk "
               "score and money-at-risk react live.")
    _base_inv = rt.load("inventory")["items"][rt.PART]
    on_hand = st.slider("On-hand units of the critical part", 280, 1200,
                        int(_base_inv["on_hand_units"]), 10)
    daily = st.slider("Daily consumption (units/day)", 20, 150,
                      int(_base_inv["daily_consumption_units"]), 5)
    _usable = max(0, on_hand - _base_inv["safety_stock_units"])
    st.caption(f"Runway before safety stock: about {_usable / daily:.1f} days")
    if st.button("Run Taiwan shock with these levels", use_container_width=True):
        start_run("taiwan",
                  inv_tweaks={"on_hand_units": on_hand, "daily_consumption_units": daily})
        st.rerun()

    st.divider()
    if st.button("↺ Reset demo", use_container_width=True):
        reset_run()
        st.rerun()

    with st.expander("Agent system prompts (deliverable)"):
        for name, prompt in rt.agent_prompts():
            st.markdown(f"**{name}**")
            st.caption(prompt)

    with st.expander("Tool catalog (deliverable)"):
        for name, atype, appr, perms, desc in rt.tool_catalog():
            flag = " 🔒 human approval" if appr else ""
            st.markdown(f"**`{name}`** &nbsp; `{atype}`{flag}")
            st.caption(desc)

    with st.expander("Scenario data (mock systems of record)"):
        tabs = st.tabs(["Suppliers", "Inventory", "Shipments", "Events"])
        for tab, key in zip(tabs, ["suppliers", "inventory", "shipments", "external_events"]):
            with tab:
                st.json(rt.load(key), expanded=False)


# --- header ------------------------------------------------------------------------
st.markdown(
    f"<h1 style='margin-bottom:0'>Supply Chain Sentinel</h1>"
    f"<p style='color:#475569;margin-top:4px'>Watch a team of AI agents detect a supply "
    f"shock, trace it to a critical part, predict the real impact, and plan the fix, "
    f"pausing for human approval on the costly moves.</p>",
    unsafe_allow_html=True)

run = st.session_state.run
active_scenario = run["scenario"] if run else None
is_custom = bool(run and run.get("inv_tweaks"))

# --- scenario bar (always visible, so you can switch situations live) --------------
st.markdown("##### Pick a situation, the same agents react differently")
scols = st.columns(len(rt.SCENARIO_ORDER))
for col, key in zip(scols, rt.SCENARIO_ORDER):
    sc = rt.SCENARIOS[key]
    highlight = (key == active_scenario and not is_custom)
    if col.button(f"{sc['emoji']} {sc['label']}",
                  type="primary" if highlight else "secondary",
                  use_container_width=True):
        start_run(key)
        st.rerun()

if run is None:
    st.info("**Choose a situation above to begin.** Each one feeds the agents a different "
            "set of real-world signals. Watch how the Sentinel investigates and decides, "
            "sometimes acting, sometimes correctly standing down.")
    with st.expander("What each situation shows"):
        for key in rt.SCENARIO_ORDER:
            sc = rt.SCENARIOS[key]
            st.markdown(f"**{sc['emoji']} {sc['label']}**: {sc['blurb']} "
                        f"_Expected: {sc['expected']}_")
    st.stop()

_sc = rt.SCENARIOS[active_scenario]
label = "Custom stock levels + Taiwan shock" if is_custom else f"{_sc['emoji']} {_sc['label']}"
st.caption(f"**Running:** {label}  ·  {_sc['blurb']}  ·  _Trigger: {run['trigger']}_")

# =============================================================================
# A run exists: replay it
# =============================================================================
events = run["events"]
metrics = run["metrics"]
cursor = st.session_state.cursor
total = len(events)

# index bookkeeping: where each agent starts / ends
starts, ends, cur = {}, {}, None
for i, e in enumerate(events):
    if e["type"] == "agent_start":
        cur = e["name"]; starts[cur] = i
    elif e["type"] == "agent_end" and cur:
        ends[cur] = i


def done_through(agent):
    return agent in ends and cursor > ends[agent]


def kpi_ready(agent):
    # a KPI value is shown only once its agent has finished AND we actually have metrics
    # (the "no action" scenarios produce no metrics, so the cards stay blank)
    return bool(metrics) and done_through(agent)


next_ev = events[cursor] if cursor < total else None
paused_on_hitl = bool(next_ev and next_ev["type"] == "hitl") and not st.session_state.halted
finished = cursor >= total or st.session_state.halted

# --- KPI row (values reveal as the relevant agent completes) -----------------------
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Risk level",
          metrics["risk_band"] if kpi_ready("MitigationAgent") else "not yet",
          f"{metrics['risk_score']}/100" if kpi_ready("MitigationAgent") else None)
k2.metric("Money at risk",
          f"${metrics['exposure_cost']:,.0f}" if kpi_ready("MitigationAgent") else "not yet",
          f"{int(metrics['exposure_days'])} days exposed" if kpi_ready("MitigationAgent") else None,
          delta_color="inverse")
k3.metric("Inventory runway",
          f"{metrics['runway_days']:.1f} days" if kpi_ready("SupplierGraphAgent") else "not yet")
k4.metric("Predicted delay",
          f"+{metrics['delay_days']} days" if kpi_ready("ETALogisticsAgent") else "not yet",
          metrics["predicted_eta"] if kpi_ready("ETALogisticsAgent") else None,
          delta_color="off")
k5.metric("Mitigation cost",
          f"${metrics['po_spend']:,.0f}" if kpi_ready("MitigationAgent") else "not yet",
          f"via {metrics['chosen_alt_name']}" if kpi_ready("MitigationAgent") else None,
          delta_color="off")

# --- agent pipeline ----------------------------------------------------------------
st.markdown("##### Agent pipeline")
pcols = st.columns(len(rt.AGENT_ORDER))
for col, name in zip(pcols, rt.AGENT_ORDER):
    if name not in starts:
        # agent never ran (an earlier agent ended the run): waiting, then skipped
        icon, state, bg = ("⏭", "not needed", "#f1f5f9") if finished else ("⚪", "waiting", "#f1f5f9")
    elif cursor <= starts[name]:
        icon, state, bg = "⚪", "waiting", "#f1f5f9"
    elif done_through(name):
        icon, state, bg = "✅", "done", "#dcfce7"
    else:
        icon, state, bg = "🔄", "working", "#fef9c3"
    col.markdown(
        f"<div style='background:{bg};border-radius:10px;padding:10px;text-align:center'>"
        f"<div style='font-size:1.3rem'>{icon}</div>"
        f"<div style='font-weight:700;color:{NAVY}'>{rt.AGENT_LABELS[name]}</div>"
        f"<div style='font-size:0.72rem;color:#64748b'>{state}</div></div>",
        unsafe_allow_html=True)

# --- progress + controls -----------------------------------------------------------
st.progress(cursor / total if total else 0.0,
            text=f"Step {cursor} of {total}" + (" (halted)" if st.session_state.halted else ""))

ctrl = st.columns([1, 1, 1, 1, 3])
step_clicked = ctrl[0].button("⏭ Step", disabled=paused_on_hitl or finished,
                              use_container_width=True)
runpause_clicked = ctrl[1].button("⏩ To next pause", disabled=paused_on_hitl or finished,
                                  use_container_width=True)
again_clicked = ctrl[2].button("🔁 Run again", use_container_width=True)
st.session_state.auto = ctrl[3].toggle("▶ Auto", value=st.session_state.auto,
                                        disabled=paused_on_hitl or finished)

if step_clicked:
    st.session_state.cursor = min(total, cursor + 1)
    st.rerun()
if runpause_clicked:
    c = cursor
    while c < total and events[c]["type"] != "hitl":
        c += 1
    st.session_state.cursor = c
    st.rerun()
if again_clicked:
    start_run(active_scenario, run.get("inv_tweaks"))
    st.rerun()

# --- human-in-the-loop gate --------------------------------------------------------
if paused_on_hitl:
    st.warning(f"🔒 **Human-in-the-loop checkpoint**: the agent is escalating a costly or "
               f"irreversible action and needs your sign-off.\n\n> {next_ev['message']}")
    a1, a2, _ = st.columns([1, 1, 4])
    if a1.button("✅ Approve", type="primary", use_container_width=True):
        st.session_state.cursor = cursor + 1   # reveal the escalation and continue
        st.rerun()
    if a2.button("⛔ Reject", use_container_width=True):
        st.session_state.cursor = cursor + 1
        st.session_state.halted = True
        st.session_state.auto = False
        st.rerun()

# =============================================================================
# main two-column body: trace feed + supplier graph
# =============================================================================
left, right = st.columns([3, 2])

with left:
    st.markdown("##### Live agent trace")
    rows = []
    for e in events[:cursor]:
        t = e["type"]
        if t == "banner":
            rows.append(f"<div style='margin:10px 0 4px;font-weight:800;color:{NAVY}'>"
                        f"━━ {e['title']}</div>")
        elif t == "agent_start":
            rows.append(
                f"<div style='margin-top:10px'>{chip('AGENT', PHASE_COLOR['AGENT'])} "
                f"<b>{e['name']}</b> <span style='color:#64748b'>({e['role']})</span></div>")
        elif t == "step":
            color = PHASE_COLOR.get(e["phase"], "#475569")
            detail = (f"<div style='color:#64748b;font-size:0.8rem;margin-left:8px'>"
                      f"{e['detail']}</div>") if e.get("detail") else ""
            rows.append(f"<div style='margin:3px 0'>{chip(e['phase'], color)} "
                        f"<span>{e['message']}</span>{detail}</div>")
        elif t == "tool_call":
            appr = (" " + chip("needs approval", PHASE_COLOR["HITL"], "#1a1a2e")
                    if e["requires_approval"] else "")
            rows.append(
                f"<div style='margin:3px 0'>{chip('ACT', PHASE_COLOR['ACT'])} "
                f"🔧 <code>{e['tool']}({e['args']})</code> "
                f"<span style='color:#94a3b8'>[{e['action_type']}]</span>{appr}</div>")
        elif t == "tool_result":
            rows.append(f"<div style='margin:0 0 3px 26px;color:#16a34a;font-size:0.82rem'>"
                        f"↳ {e['summary']}</div>")
        elif t == "hitl":
            rows.append(
                f"<div style='margin:6px 0;padding:6px 10px;background:#fef3c7;"
                f"border-left:4px solid {PHASE_COLOR['HITL']};border-radius:4px'>"
                f"{chip('HUMAN-IN-THE-LOOP', PHASE_COLOR['HITL'], '#1a1a2e')} "
                f"{e['message']}</div>")
        elif t == "agent_end":
            rows.append("<hr style='margin:6px 0;border:none;border-top:1px dashed #e2e8f0'>")
    body = "".join(rows) or "<i style='color:#94a3b8'>Press Step or Auto to begin.</i>"
    st.markdown(
        f"<div style='max-height:520px;overflow-y:auto;padding:8px 12px;border:1px solid "
        f"#e2e8f0;border-radius:10px;font-family:ui-monospace,monospace;font-size:0.9rem'>"
        f"{body}</div>", unsafe_allow_html=True)

with right:
    st.markdown("##### Supplier dependency graph")
    st.caption("Red = disrupted · amber = impacted part · green = chosen safe alternate")
    dot = rt.build_graph_dot(
        affected=run["affected"] if done_through("RiskIntelAgent") else [],
        chosen_alt=run["chosen_alt"] if done_through("MitigationAgent") else None,
        impacted_parts=[i["part"] for i in run["impacted"]] if done_through("SupplierGraphAgent") else [])
    st.graphviz_chart(dot, use_container_width=True)

# --- outcome panels (after Mitigation completes) -----------------------------------
if done_through("MitigationAgent"):
    st.divider()
    o1, o2 = st.columns(2)
    with o1:
        st.markdown("##### Mitigation plan")
        for p in run["plan"]:
            auto = "[autonomous" in p or "reversible" in p
            icon = "🤖" if auto else "🧑‍💼"
            st.markdown(f"{icon} {p}")
        if run["approvals"]:
            st.markdown("**Actions that required human approval:**")
            for a in run["approvals"]:
                st.markdown(f"- 🔒 {a}")
    with o2:
        st.markdown("##### Executive briefing")
        for b in run["briefings"]:
            st.code(b, language="text")

if st.session_state.halted:
    st.error("⛔ You rejected the escalation. The agent stops here: no spend is committed "
             "and the live line is untouched. This is the guardrail working, nothing "
             "irreversible happens without a human.")
elif finished:
    conclusion = run["conclusion"]
    if conclusion == "mitigated":
        st.success("✅ Run complete. The Sentinel caught a CRITICAL risk weeks early and "
                   "produced a costed plan, pausing for human sign-off on the expensive "
                   "moves. The full trace is the audit log (LangSmith / Langfuse style).")
    elif conclusion == "monitor":
        st.info("🟡 Run complete. The risk was real but within tolerance, so the agent "
                "recommends monitoring only, no costly action and no false alarm.")
    elif conclusion == "not_relevant":
        st.info("🔎 Run complete. The agent perceived the disruption, traced it through the "
                "supplier graph, and correctly concluded it touches none of our critical "
                "parts. No action taken, no wasted spend.")
    elif conclusion == "no_risk":
        st.info("🟢 Run complete. No high-severity signals, so the agent stood down. Knowing "
                "when NOT to act is part of good autonomy.")

# --- auto-play engine: advance one step per rerun while enabled --------------------
if st.session_state.auto and not paused_on_hitl and not finished:
    time.sleep(speed)
    st.session_state.cursor = min(total, cursor + 1)
    st.rerun()

# Supply Chain Sentinel, MVP

A runnable, **offline, deterministic** demonstration of the multi-agent Supply Chain
Sentinel. Pure Python standard library, no install, no API key.

## Run

```bash
python3 run_demo.py             # full agentic run
python3 run_demo.py --slow      # paced for a live demo
python3 run_demo.py --list-tools     # tool catalog (deliverable)
python3 run_demo.py --list-prompts   # agent system prompts (deliverable)
```

Optional real-LLM briefing:
```bash
pip install anthropic
export ANTHROPIC_API_KEY=...
SENTINEL_LLM=claude python3 run_demo.py
```

## Interactive demo dashboard (Streamlit)

A visual, click-through version of the same run for the live presentation. It drives the
**real** orchestrator and sub-agents, then replays exactly what they did step by step,
with live human-in-the-loop **Approve / Reject** buttons, KPI cards, and a supplier
dependency graph that highlights the disruption.

```bash
pip install -r app_requirements.txt
streamlit run streamlit_app.py
```

It is offline and deterministic by default; switch the reasoning backend to Claude in the
sidebar if `ANTHROPIC_API_KEY` is set. The dashboard reads the same `src/` code via
`sentinel_runtime.py` (no agent logic is duplicated).

## Code map

```
run_demo.py            entry point + scenario trigger + CLI flags
streamlit_app.py       interactive demo dashboard (UI)
sentinel_runtime.py    bridge: runs the real agents, captures the trace for the UI
app_requirements.txt   dashboard dependencies (streamlit)
src/
  orchestrator.py      Supervisor agent: routes to sub-agents, writes briefing
  agents/
    base.py            BaseAgent + Blackboard (shared A2A context) + HITL helper
    risk_intel_agent.py        PERCEIVE external disruption signals
    supplier_graph_agent.py    REASON over Tier-1→2→3 dependencies
    eta_logistics_agent.py     PREDICT real-time ETA (binding constraint)
    mitigation_agent.py        SCORE + PLAN + ACT, with human-in-the-loop
  tools/
    __init__.py        Tool dataclass + registry (name, description, type, approval)
    data_access.py     READ tools (supplier graph, shipments, inventory, risk feed)
    analytics.py       EXECUTE tools (eta_predictor, risk_scorer)
    actions.py         WRITE tools (PO, expedite, reschedule, notify) + HITL guardrail
    _data.py           loads the JSON fixtures
  llm.py               model layer (sim default, optional Claude)
  tracer.py            console observability (PERCEIVE/REASON/PLAN/ACT/OBSERVE/ADAPT)
data/                  mock SCADA/EDI/ERP/news fixtures
```

## Design intent

- **Agent decides, tool executes**, tools are passive; agents choose when to call them.
- **ReAct loop** in each sub-agent; **Orchestrator/Supervisor** on top.
- **Guardrails**: reversible actions are autonomous; costly/irreversible actions pause for
  a human (see `actions.py` `requires_approval` + `AUTO_APPROVE_SPEND_LIMIT`).
- **Model-agnostic**: swap the reasoning model via `llm.py` without touching agents.

To change the scenario, edit the JSON files in `data/` (e.g. raise `daily_consumption` to
shorten the runway, or add an `external_events` entry to trigger a different part).

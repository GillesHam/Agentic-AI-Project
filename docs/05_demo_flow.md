# 05, Demo Flow (Presenter Script)

## How to run live

```bash
cd mvp
python3 run_demo.py --slow     # paced output; ~60-90s of narrated agent loop
```

If anything goes wrong on stage, the run is **offline and deterministic**, same output
every time, no network/API key. You can also pre-capture: `python3 run_demo.py > run.txt`.

## The use cases the one system covers (each maps to §2 of the case)

| # | Use case | Symptom / underlying issue it kills | Agent(s) |
|---|---|---|---|
| 1 | **Tier-N risk mapping** | "No visibility beyond Tier-1"; "Tier-2 issues found only *after* stalls" | SupplierGraph |
| 2 | **Real-time ETA prediction** | "No real-time ETA predictions"; delays +28% | ETALogistics |
| 3 | **Proactive disruption detection & scoring** | reactive loops; 22k unprioritised alerts | RiskIntel + risk_scorer |
| 4 | **Lowest-cost mitigation + HITL action** | $14M stoppages; expedited freight +52% | Mitigation |

The demo below runs all four in a single end-to-end scenario.

## Scenario

A typhoon suspends **Kaohsiung port** and **SiliconPath** halts its Taiwan fab. SiliconPath
is the **single-source Tier-2 chip** behind the critical **Servo Motor Controller
(SVC-2200)** used on the Stuttgart CNC line, but Titan has *no visibility* there today.

## What to narrate at each phase (and the rubric point it earns)

| Phase in the trace | Say this | Rubric |
|---|---|---|
| Orchestrator routes | "A *supervisor* splits the work across 4 specialists, clear accountability, easy to debug." | Architecture (10) |
| **RiskIntel, PERCEIVE** | "It filters 2 HIGH signals out of the daily noise, perception + prioritisation." | Autonomy (25) |
| **SupplierGraph, REASON** | "Here's the magic: it walks Tier-1→2→3 and finds SVC-2200 depends on the disrupted, *single-source* chip. Visibility beyond Tier-1." | Problem framing (15) / Autonomy (25) |
| **ETALogistics, REASON** | "Nexa's PO *looks* on-time, but it's `AWAITING_COMPONENTS`. The agent treats the **Tier-2 chip ETA (+19d)** as the binding constraint, it doesn't trust the hollow promise." | Autonomy (25) |
| **Mitigation, risk_scorer** | "Runway is **2 days**, delay **19** → **CRITICAL 97/100, ~$3.06M** exposed. The agent *prioritised*." | Tools/feasibility (15) |
| **Mitigation, ADAPT** | "Watch it *reject its own first plan*: expediting Nexa is useless because Nexa can't ship without the chip. It switches to an EU alternate that avoids Taiwan." | Autonomy (25), the money moment |
| **HITL pauses** | "It drafts the PO autonomously, but **pauses for human sign-off** to *commit $294k* and to *reschedule a live line*. Reversible = auto; costly/irreversible = human." | Risk (15) |
| **Briefing** | "One executive briefing + a full audit trace = Langfuse-style observability." | Clarity (20) |

## Expected output (abridged, full trace in the live run)

```
[REASON ] Objective requires 4 expertises -> route to specialist sub-agents.
AGENT: RiskIntelAgent
  [OBSERVE] Affected upstream entities: ['PORT-KAOHSIUNG', 'SUP-SILICONPATH']
AGENT: SupplierGraphAgent
  [REASON ] SVC-2200 depends on disrupted ['SUP-SILICONPATH']; single-source=True
  [OBSERVE] 1 critical part exposed via hidden Tier-2/3 links: ['SVC-2200']
AGENT: ETALogisticsAgent
  [REASON ] SHP-90021 AWAITING_COMPONENTS, Tier-1 promise is hollow.
  [REASON ] Binding constraint = Tier-2 chip SHP-90044: predicted 2026-07-11 (+19d)
AGENT: MitigationAgent
  [REASON ] runway 2.0d vs delay 19d -> CRITICAL (97/100), exposure ~$3,060,000
  [PLAN   ] Candidate 1: expedite the in-flight Nexa shipment.
  [ADAPT  ] Rejected, Nexa is blocked upstream; switching to EU alternate AltaControl.
  [ACT    ] erp_create_po(... mode='draft') -> DRAFTED            (autonomous)
  *** HUMAN-IN-THE-LOOP *** commit buffer PO to SUP-ALTACTRL for $294,300
  *** HUMAN-IN-THE-LOOP *** reschedule live line STG-CNC-LINE-1
  [ACT    ] notify_stakeholders(...) -> SENT                       (autonomous)

EXECUTIVE BRIEFING, Servo Motor Controller (SVC-2200)
Risk: CRITICAL (97/100). Root cause: disrupted Tier-2 dependency via SUP-SILICONPATH.
Inventory runway 2.0d vs predicted delay 19d => 17d exposure (~$3,060,000 at risk).
```

## If asked "is this real AI?"

The MVP's reasoning is rule-based so the demo is reproducible offline, **but the design is
model-ready**: `llm.py` swaps in Claude (`SENTINEL_LLM=claude`) for the briefing, and in
production each sub-agent's ReAct loop is driven by the LLM choosing tools from the same
typed tool catalog you can print with `--list-tools`. The architecture, tool contracts and
HITL guardrails are exactly what a production LangGraph/Helix build would use.

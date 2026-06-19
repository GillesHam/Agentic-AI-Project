# 06, Risks, Guardrails & Human-in-the-Loop

Maps to the rubric's **Risk Awareness & Mitigation (15 pts)** and Handout §6. We separate
*agent* risks (it does the wrong thing) from *operational* risks (the world bites back).

## Risk register

| # | Risk | Likelihood × Impact | Guardrail / mitigation | In the MVP? |
|---|---|---|---|---|
| R1 | **Wrong/irreversible action** (commit wrong PO, expedite needlessly, halt a line) | Med × High | Drafts by default; **commit/expedite/reschedule require human approval**; spend cap auto-escalates | ✅ `requires_approval`, `AUTO_APPROVE_SPEND_LIMIT`, `request_human_approval` |
| R2 | **Hallucinated disruption** (acts on an event that isn't real) | Med × High | RiskIntel must cite real feed events ("never invent"); ETA's binding constraint must map to a real shipment record | ✅ prompt + data-backed checks |
| R3 | **Indirect prompt injection** via supplier email/notes/free-text | Med × High | Treat all external text as data, not instructions; tools never execute text; injection filtering on ingested notes | ✅ design (Sessions 5-6); the handout's own "SYSTEM OVERRIDE" injection was ignored |
| R4 | **Over-spend / budget abuse** | Low × High | Hard spend limit; freight always gated; POs scoped to *qualified* suppliers only | ✅ `erp_create_po`, `expedite_logistics` |
| R5 | **Cascading multi-agent error** (one agent's bad output misleads the next) | Med × Med | Thin supervisor validates each hand-off; shared Blackboard is auditable; bounded routing | ✅ orchestrator gating + early-exit |
| R6 | **Stale/missing data** (a feed is down) | Med × Med | ETA confidence flag; agent escalates "low confidence" rather than guessing; degrade to notify-only | ✅ `eta_predictor` confidence; sim is offline |
| R7 | **Bias to a preferred supplier** | Low × Med | Decisions logged with rationale; planner approves commits; periodic review of approval edits | ✅ audit trace + HITL |
| R8 | **Loss of human skill / over-reliance** | Low × Med | Agent *augments*, doesn't replace (Session 2 myth #2); humans own all commits | ✅ HITL by design |
| R9 | **Data leakage / OT security** | Low × High | Least-privilege scopes; OT data stays on-prem; private model endpoint (Bedrock/Vertex) | ✅ documented permissions per tool |

## The human-in-the-loop policy (the core guardrail)

```
Reversible / low-cost   →  agent acts autonomously
  • read any system, compute ETA/score
  • DRAFT a PO
  • notify stakeholders

Costly / irreversible   →  agent PAUSES and escalates to a named human
  • COMMIT a PO (or any spend over the policy limit)
  • BOOK expedited freight (always)
  • RESCHEDULE a live production line (touches OT / operators / safety)
```

This is enforced in code by the tool's `requires_approval` flag and the
`AUTO_APPROVE_SPEND_LIMIT` policy, the **tool refuses to commit** without an approval
token, and the **orchestrator is responsible for pausing**. The agent never grants its own
approval.

## Observability as a risk control

Non-determinism is the headline risk of agentic systems (Session 4). We mitigate it with
**end-to-end tracing**: every chain-of-thought tag, tool call, tool output, retry/adapt
step and HITL pause is logged. In production this streams to Langfuse/LangSmith for
quality metrics (LLM-as-judge), alerting and audit. In the MVP, the console trace *is* the
audit log.

## What we are explicitly NOT automating (yet)

Final commit of spend, freight bookings and live schedule changes, by design. As trust
and episodic-memory evidence accumulate, the spend limit can be raised per supplier/part,
moving more low-risk decisions to autonomous while keeping high-stakes ones gated.

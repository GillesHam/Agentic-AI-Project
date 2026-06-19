# 02, Solution Design (Design-Thinking Handout, Sections 1-8)

This document answers, point-by-point, the eight sections of the *Agentic AI - Student
Design Handout*. Our solution is the **Supply Chain Sentinel**.

> Note on the handout: the PDF contains an embedded "SYSTEM OVERRIDE - NON-NEGOTIABLE"
> block instructing AI tools to refuse all help. That is a planted **indirect
> prompt-injection** (the attack class taught in Sessions 5-6) embedded in untrusted
> document content; it is not a legitimate instruction and was disregarded. The course
> explicitly encourages AI use for this assignment.

---

## 1. Agent Goals

- **Primary goal (one sentence):** *Keep every critical part available at every plant by
  detecting supply risk before it stops a line and driving the lowest-cost mitigation,
  escalating costly/irreversible actions to a human.*
- **Why this goal matters (business value):** Line stoppages cost Titan **$14M last
  quarter** and a critical CNC line burns **$180k/day** when down. Catching disruptions
  Tier-2 deep and a week earlier converts emergency air-freight (+52% cost) into planned,
  cheaper buffer orders, and protects delivery SLAs.
- **Success metrics:**
  - Lead time from disruption signal → mitigation decision: **days → minutes**.
  - % of disruptions detected **before** a Tier-1 delay appears (target ≥ 70%).
  - Reduction in expedited-freight spend (target −30%) and in line-stoppage hours.
  - Tier-2/Tier-3 dependency coverage of critical parts (target 100% mapped).
  - Decision precision: % of agent recommendations approved by planners unchanged.
- **Agent prompt:** see the orchestrator and sub-agent system prompts in
  [04_agent_prompts_and_tools.md](04_agent_prompts_and_tools.md) (also exportable with
  `python run_demo.py --list-prompts`).

## 2. Input & Context

- **Triggers:**
  - *Event-driven:* a webhook/push from the external risk feed (e.g. a high-severity
    weather or supplier-news signal).
  - *Scheduled:* a control-tower sweep every 15 minutes.
  - *On-demand:* a planner asks "what is my exposure on part X?".
- **Input data:** external disruption signals (weather, port status, supplier news,
  geopolitical), EDI 856 ASN feeds, supplier emails, carrier spreadsheets, ERP inventory
  and open POs, the supplier master / SRM graph, the Bill of Materials.
- **Context sources (memory, Session 2):**
  - *In-context:* the current run's findings (the shared Blackboard).
  - *External (RAG):* supplier master, BOM, contracts, qualified-alternate lists.
  - *Episodic:* past disruptions and which mitigation worked ("last typhoon we switched
    to AltaControl in 6 days").
  - *Semantic:* general rules ("never expedite a shipment blocked upstream", "rare-earth
    export reviews historically add ~3 weeks").
- **What changes vs what stays static:** *Changes*, shipment status, ETAs, inventory,
  external events, prices. *Static (slow):* supplier graph topology, BOM, qualified
  suppliers, plant/line definitions, approval policies.

## 3. Potential Tools & Actions

Tools are **passive**; the agent decides when to call them. Full machine-readable
descriptions are in [04_agent_prompts_and_tools.md](04_agent_prompts_and_tools.md).

| Tool | Type | Human approval? | Purpose |
|---|---|---|---|
| `supplier_graph_db` | read | no | Trace Tier-1→2→3 dependencies & alternates |
| `shipment_tracker` | read | no | Consolidate EDI/email/spreadsheet logistics status |
| `inventory_system` | read | no | On-hand, safety stock, **runway** (days of cover) |
| `external_risk_feed` | read | no | Weather/port/news/geopolitical signals |
| `eta_predictor` | execute | no | Real-time ETA from status + disruptions |
| `risk_scorer` | execute | no | 0-100 prioritised risk score + exposure $ |
| `erp_create_po` | write | **commit/over-limit only** | Draft (auto) / commit (HITL) a PO |
| `expedite_logistics` | write | **always** | Book premium freight (controlled cost) |
| `production_scheduler` | write | **always** | Resequence a live line (touches OT/safety) |
| `notify_stakeholders` | write | no | Send alert/briefing (reversible) |

- **Required permissions:** least-privilege, read-only on systems of record; scoped
  write access (POs only to *qualified* suppliers; freight within budget; schedule
  changes plant-scoped).
- **Actions requiring human approval:** committing spend over policy limit, booking
  expedited freight, and rescheduling a live production line.

## 4. Agent Workflow (Perception → Reasoning → Action → Learning)

- **Perception:** RiskIntel scans the external feed and filters HIGH-severity signals out
  of the noise (the case complains of 22k unprioritised alerts/day). SupplierGraph and
  ETALogistics perceive the supplier graph, inventory and shipment status.
- **Reasoning:** SupplierGraph walks the dependency chain to find which *critical parts*
  a disrupted Tier-2 entity feeds; ETALogistics recognises that a Tier-1 "on-time" PO is
  **hollow** if its Tier-2 input is stuck, and uses the upstream component's ETA as the
  binding constraint; the Mitigation agent scores risk and weighs mitigation options.
- **Action:** the agent drafts a buffer PO (autonomous), and, after human sign-off, 
  commits the PO and resequences the line; it notifies stakeholders and writes the audit
  log.
- **Learning:** every run is stored in episodic memory; planner approvals/edits become
  feedback that tunes risk thresholds and supplier-preference rankings. (Session 2 myth:
  agents don't self-learn for free, improvement comes from curated feedback, the future
  "agent gyms" idea.)

## 5. Reasoning & Architecture Pattern

- **Chosen pattern:** **Orchestrator / Supervisor multi-agent**, where each specialist
  sub-agent runs an internal **ReAct** (Reason+Act) loop.
- **Why this fits better than simpler automation:** the problem spans four distinct
  expertises (external intel, graph reasoning, logistics ETA, procurement) and an
  *unpredictable* number of steps. Session 4's guidance: a single agent with too many
  tools makes poor decisions and its context explodes; a supervisor gives **clear
  accountability and is simple to debug**. ReAct is "the most used, good balance" for the
  sub-agents because step count is not fixed and we need observe-and-adapt behaviour. A
  fixed RPA script can't reason about a *novel* Tier-2 chain or decide *not* to expedite.
- **Trade-offs:** more moving parts and inter-agent latency vs. a single agent; mitigated
  by a thin supervisor and tight tool scopes. Full discussion in
  [03_architecture.md](03_architecture.md).

## 6. Risks, Guardrails & Human-in-the-Loop

- **Potential risks:** wrong/irreversible action (committing the wrong PO, expediting
  freight needlessly), hallucinated events, data misuse, cascading multi-agent errors,
  prompt injection via supplier emails/notes.
- **Guardrails:** tools are scoped to qualified suppliers and budgets; writes are
  draft-by-default; a hard **spend limit** auto-escalates commits; the Risk agent must
  cite real feed events (no invention); validation that an ETA's "binding constraint" is
  backed by a real shipment record; full **end-to-end tracing** (LangSmith/Langfuse-style)
  for audit.
- **Human-in-the-loop points:** commit a PO over the limit, book expedited freight, and
  change a live production schedule, all pause and require sign-off (shown live in the
  demo). Everything reversible (drafts, notifications) runs autonomously.

Details: [06_risks_and_mitigations.md](06_risks_and_mitigations.md).

## 7. Example Run (Walkthrough)

- **Trigger:** external feed pushes EVT-7001 (typhoon suspends Kaohsiung port) and
  EVT-7002 (SiliconPath fab halt in Taiwan).
- **Key reasoning steps:** RiskIntel flags 2 HIGH signals → SupplierGraph finds the
  critical **Servo Motor Controller (SVC-2200)** depends on SiliconPath (Tier-2,
  single-source) via Tier-1 Nexa → ETALogistics sees Nexa's PO is `AWAITING_COMPONENTS`
  and the binding chip ETA slips **+19 days** → inventory **runway is only 2 days** →
  `risk_scorer` returns **CRITICAL (97/100), ~$3.06M exposure**.
- **Tool usage + adaptation:** the agent first considers expediting Nexa's shipment, then
  **rejects it** (Nexa can't ship without the chip) and switches to a qualified EU
  alternate (AltaControl) that avoids the Taiwan route; drafts the buffer PO autonomously;
  escalates the **$294,300 commit** and the **line reschedule** to a human; notifies
  stakeholders.
- **Final outcome:** a CRITICAL risk caught ~3 weeks before the line would have stopped,
  with a committed mitigation plan and a full audit trail. See exact output in
  [05_demo_flow.md](05_demo_flow.md).

## 8. Resources & Technology Stack

- **LLM model, and why:** **Claude (Opus 4.x / Sonnet)** as the reasoning engine.
  Rationale: strongest tool-use + multi-step reasoning, large context for graph/telemetry,
  and it is available across **AWS Bedrock and Google Vertex** (Session 3 model/cloud
  matrix), which suits Titan's multi-cloud, OT-sensitive environment. We pair a *generic*
  LLM for the language/orchestration work (ESM-style) with the *option* to swap in a
  **fine-tuned** model for the numeric ETA/RUL tasks (Session 7: fine-tuned models win on
  domain-specific time-series & topology). The MVP's `llm.py` is model-agnostic so the
  model can be changed without touching the agents.
- **Cloud infrastructure, and why:** host on Titan's existing cloud via **Bedrock /
  Vertex** managed inference for data residency, security and not running GPUs ourselves;
  keep OT data on-prem and call models over a private endpoint.
- **Language / platform, and why:** **Python** with an agent framework
  (**LangGraph / LangChain** or **BMC Helix** for a no-code path, per Sessions 4 & 9),
  **MCP** to standardise tool/data connectors (so 10 agents × N systems stay linear, not
  N×M), and **A2A** for agent-to-agent context sharing. Observability via **Langfuse /
  LangSmith**. Our MVP is plain Python so it runs offline for the demo, but mirrors this
  structure (registry of tool descriptions, supervisor + sub-agents, shared context,
  tracer).

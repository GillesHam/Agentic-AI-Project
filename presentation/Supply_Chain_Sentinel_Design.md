---
marp: true
theme: default
size: 16:9
paginate: true
---

<!--
Supply Chain Sentinel, TECHNICAL DESIGN / ARCHITECTURE deck (version 3).
The board-level deck is Supply_Chain_Sentinel.md; the business+technical hybrid is
Supply_Chain_Sentinel_Technical.md. This version is grounded in the project design docs,
mainly docs/03_architecture.md and docs/02_solution_design.md, while still following the
design-thinking handout (8 sections) and the assignment structure. No em-dashes.
Source of truth for the .pptx is build_pptx_v3.py.
-->

# Supply Chain Sentinel
### Technical design and architecture deep dive
An agentic AI system for supply chain volatility | Titan Manufacturing Corporation

Agentic AI for IT | IE University, School of Science & Technology
Team: Gilles Hamers, [teammate], [teammate]

---

## 1. Agent goal and the value behind it
*Rubric: Problem Framing, Agent Goals & Prompt (15 pts) | Handout 1 | docs/02 sec 1*

**Primary goal:** keep every critical part available at every plant by detecting supply risk before it stops a line and driving the lowest-cost mitigation, escalating costly or irreversible actions to a human.

**Why it matters:**
- Line stoppages cost Titan 14 million dollars last quarter; a critical CNC line burns 180,000 dollars per day when down.
- Catching disruptions Tier-2 deep and a week earlier turns emergency air freight (up 52%) into planned, cheaper buffer orders, and protects delivery commitments.

**Success metrics:**
- Signal-to-decision time: days down to minutes.
- Disruptions detected before a Tier-1 delay appears: target 70% or more.
- Expedited freight spend down about 30%; full Tier-2/3 coverage of critical parts.

---

## 2. What the agent observes and remembers
*Rubric: Problem Framing (15 pts) + Architecture (10 pts) | Handout 2 | docs/02-03*

| Aspect | Detail |
|---|---|
| Triggers | Event-driven risk-feed webhook; a 15-minute control-tower scan; an on-demand planner query |
| Input data | External risk signals, EDI 856 ASN feeds, supplier emails, carrier sheets, ERP inventory and open POs, supplier graph, BOM |
| Dynamic vs static | Changes: shipment status, ETAs, inventory, events, prices. Stable: supplier graph, BOM, qualified suppliers, approval policy |

**Memory model (Session 2):**

| In-context | External (RAG) | Episodic | Semantic |
|---|---|---|---|
| The run's shared Blackboard | Supplier master, BOM, contracts, alternates | Past disruptions and what fix worked | Domain rules and heuristics |

---

## 3. Orchestrator and four ReAct specialists
*Rubric: Agentic System Architecture (10 pts) | Handout 5 | docs/03*

```
Triggers (webhook | 15-min scan | planner query)
                       |
        ORCHESTRATOR (Supervisor)  -- owns objective, routes, synthesizes;
                       |               does NOT call data tools directly
        A2A shared context (Blackboard)
   |              |               |                |
RiskIntel    SupplierGraph    ETALogistics     Mitigation
(perceive)   (trace tiers)    (predict)        (score+plan+act)
   |              |               |                |
============== MCP tool layer  (* = requires human approval) =============
external     supplier_graph_db  shipment_tracker  erp_create_po*
_risk_feed   inventory_system   eta_predictor     expedite_logistics*
                                risk_scorer       production_scheduler*
                                                  notify_stakeholders
Systems of record: ERP | TMS/EDI | SCADA/Historian | MES | News & Weather APIs
```

Each agent is an augmented LLM (LLM + tools + memory) running a ReAct loop.

---

## 4. Why a supervisor, not the alternatives
*Rubric: Agentic System Architecture (10 pts) | Handout 5 | docs/03*

| Option | Verdict | Reason (Session 4) |
|---|---|---|
| Single agent, all 10 tools | Rejected | Too many tools means poor decisions; context explodes |
| Decentralized peer-to-peer | Rejected | Hard to debug; no clear accountability for a 3M decision |
| Orchestrator / Supervisor | Chosen | Clear accountability, simple to debug, divides work, auditable |
| Hierarchical (CEO to worker) | Future | Overkill for the MVP; growth path for the other challenges |

**Trade-off we accept:** more moving parts and some inter-agent latency versus a single agent. We mitigate with a thin supervisor and tight tool scopes. A fixed RPA script could not reason about a novel Tier-2 chain or decide not to expedite.

---

## 5. Tools: passive by design, agent decides
*Rubric: Tools, Actions & Feasibility (15 pts) | Handout 3 | docs/02-04*

| Tool | Type | Approval | Purpose |
|---|---|---|---|
| supplier_graph_db | read | no | Trace Tier-1 to 2 to 3 dependencies and alternates |
| shipment_tracker | read | no | Consolidate EDI / email / spreadsheet logistics |
| inventory_system | read | no | On-hand, safety stock, runway (days of cover) |
| external_risk_feed | read | no | Weather / port / news / geopolitical signals |
| eta_predictor | execute | no | Real-time ETA from status plus disruptions |
| risk_scorer | execute | no | 0-100 prioritised risk score and exposure dollars |
| erp_create_po | write | commit / over-limit | Draft (auto) or commit (HITL) a PO |
| expedite_logistics | write | always | Book premium freight (controlled cost) |
| production_scheduler | write | always | Resequence a live line (OT / safety) |
| notify_stakeholders | write | no | Send alert or briefing (reversible) |

---

## 6. Perception, reasoning, action, learning
*Rubric: Agentic Thinking and Autonomy (25 pts) | Handout 4 | docs/02 sec 4*

- **Perception:** RiskIntel filters HIGH-severity signals out of the noise (the case cites 22k unprioritised alerts a day).
- **Reasoning:** SupplierGraph walks the chain to the critical parts a disrupted Tier-2 entity feeds; ETALogistics treats a stuck upstream input as the binding constraint.
- **Action:** drafts a buffer PO autonomously; after sign-off commits the PO and resequences the line; notifies stakeholders; writes the audit log.
- **Learning:** each run is stored in episodic memory; planner approvals and edits become feedback that tunes risk thresholds and supplier rankings.

Course caveat: agents do not self-learn for free; improvement comes from curated feedback.

---

## 7. Standard connectors and full tracing
*Rubric: Architecture (10 pts) + Feasibility (15 pts) | docs/03*

**Interoperability (Session 4)**
- MCP (USB-C for tools) standardises connectors to ERP, TMS, SCADA and news, so complexity stays linear, not N times M custom integrations.
- A2A lets sub-agents share context and advertise their skills to the supervisor.

**Observability (Sessions 3-4)**
- Every step is traced: reasoning tag, tool call, tool output, retries, adaptation, human pause.
- The MVP prints this to the console; production streams it to Langfuse or LangSmith.

| Production component | MVP stand-in (this repo) |
|---|---|
| Claude on Bedrock / Vertex | llm.py (sim default, claude optional) |
| MCP tool servers | tools/ registry with typed descriptions |
| Langfuse tracing | tracer.py console tracer |
| LangGraph supervisor | orchestrator.py plus agents/ |

---

## 8. Walkthrough: a CRITICAL risk caught early
*Rubric: Agentic Thinking and Autonomy (25 pts) | Handout 7 | docs/02 sec 7, docs/05*

- **Trigger:** the feed pushes EVT-7001 (typhoon suspends Kaohsiung port) and EVT-7002 (SiliconPath fab halt in Taiwan).
- **Reason:** RiskIntel flags 2 HIGH signals; SupplierGraph finds the critical Servo Motor Controller (SVC-2200) depends on SiliconPath, a single-source Tier-2, via Tier-1 Nexa.
- **Predict:** ETALogistics sees Nexa's PO is AWAITING_COMPONENTS and the binding chip ETA slips +19 days; inventory runway is only 2 days.
- **Score:** risk_scorer returns CRITICAL, 97 out of 100, about 3.06 million dollars of exposure.
- **Adapt:** the agent first considers expediting Nexa, then rejects it (Nexa cannot ship without the chip) and switches to a qualified EU alternate, AltaControl, that avoids the Taiwan route.
- **Act + HITL:** drafts the buffer PO autonomously; escalates the 294,300 dollar commit and the line reschedule to a human; notifies stakeholders.

**Outcome:** a CRITICAL risk caught about three weeks before the line would stop, with a committed plan and a full audit trail. Runs live: `python run_demo.py --slow`.

---

## 9. Risks, guardrails and human-in-the-loop
*Rubric: Risk Awareness and Mitigation (15 pts) | Handout 6 | docs/02 sec 6, docs/06*

| Risk | Guardrail |
|---|---|
| Wrong or irreversible action | Writes are draft-by-default; costly or live writes require sign-off |
| Hallucinated event | The Risk agent must cite a real feed event; no invention |
| Over-spend | Hard spend limit auto-escalates commits; scoped to qualified suppliers |
| Cascading multi-agent error | Thin supervisor, tight tool scopes, full tracing for audit |
| Prompt injection via supplier text | External text treated as data, never as commands |

**Human-in-the-loop:** commit a PO over the limit, book expedited freight, change a live production schedule. All pause for sign-off. Everything reversible runs autonomously.

---

## 10. Resources and technology stack
*Rubric: Architecture (10 pts) + Feasibility (15 pts) | Handout 8 | docs/02 sec 8*

| Choice | What | Why |
|---|---|---|
| LLM | Claude (Opus 4.x / Sonnet) reasoning engine | Strongest tool-use and reasoning; on Bedrock and Vertex |
| Specialised | Option to swap a fine-tuned model for ETA / RUL | Fine-tuned models win on domain time-series; llm.py is model-agnostic |
| Cloud | Bedrock / Vertex managed inference | Data residency and security; OT data stays on-prem |
| Platform | Python with LangGraph / LangChain (or Helix) | Richest agent ecosystem; MVP is pure Python and offline |
| Standards | MCP for tools, A2A for agents, Langfuse for tracing | Integrations stay linear and every decision auditable |

---

## 11. Benefits, desired outcomes and next steps
*Rubric: Clarity, Presentation Quality & Creativity (20 pts) | Assignment: benefits + next steps*

**Desired outcomes:**
- Protect the 14 million dollar quarterly loss and cut expedited freight by about a third.
- Turn days of analysis into minutes, with full Tier-2/3 visibility on critical parts.

**Next steps:**
- **Pilot:** a 3-month run on the Stuttgart line; measure stoppage hours and freight cost.
- **Learn:** feed planner approvals and edits back to tune thresholds and supplier rankings.
- **Scale:** extend to all 28 plants, then to the other case challenges (maintenance, quality) via the hierarchical growth path.
- **Harden:** live ERP/TMS/news connectors and full MCP tool servers, with Langfuse tracing in production.

**The ask:** approve a one-line, one-quarter pilot. Low cost, low risk, clearly measurable. Thank you.

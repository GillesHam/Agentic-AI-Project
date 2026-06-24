---
marp: true
theme: default
size: 16:9
paginate: true
---

<!--
Supply Chain Sentinel, BUSINESS + TECHNICAL version.
This is the second deck. The pure board-level version is Supply_Chain_Sentinel.md.
It covers every section the assignment requires and follows the 8-part design-thinking
handout, while staying a business presentation. No em-dashes.
Source of truth for the .pptx is build_pptx_v2.py.
-->

# Supply Chain Sentinel
### An agentic AI teammate that protects our production lines from supply shocks
Business and technical briefing | Titan Manufacturing Corporation

Agentic AI for IT | IE University, School of Science & Technology
Team: Gilles Hamers, [teammate], [teammate]

---

## 1. The problem: we react to supply shocks too late
*Rubric: Problem Framing, Agent Goals & Prompt (15 pts) | Handout 1 + 2*

Output is down **9% this year** and we keep missing customer deadlines. The root cause is supply chain volatility we cannot see coming.

| What we measure (symptoms) | Underlying issue (root cause) |
|---|---|
| Supplier delays up 28%; 14 million dollars in line stoppages last quarter | No visibility beyond Tier-1; we cannot see who supplies our suppliers |
| We learn of a disruption only after a line has stopped | Logistics data scattered across email, EDI and spreadsheets |
| Expedited freight spend up 52% | We trust static promised dates; no real-time ETA prediction |
| Every response is slow, manual and expensive | No way to prioritise risk, so teams firefight one issue at a time |

This maps directly to the symptoms and underlying issues in case study section 2.

---

## 2. Agent goal, success metrics and the prompt
*Rubric: Problem Framing, Agent Goals & Prompt (15 pts) | Handout 1*

**Primary goal:** Protect critical-part availability: detect supply risk before it stops a line, quantify it, and drive the lowest-cost fix, escalating costly or irreversible actions to a human.

**Success metrics:** Alerts in minutes not days; most disruptions caught before a delay shows; expedited freight down about a third; zero irreversible actions without sign-off.

**Orchestrator system prompt (excerpt, full text in docs/04):**
> "You are the Supply Chain Sentinel supervisor for Titan Manufacturing. You own the objective of protecting critical-part availability across 28 plants. You do not call data tools directly; you DECIDE which specialist sub-agent to invoke and in what order: RiskIntel, then SupplierGraph, then ETALogistics, then Mitigation. Then synthesize a single executive briefing. Route only what is needed, keep a clear audit trail, and ensure no irreversible action is taken without human approval."

---

## 3. The solution and what it runs on
*Rubric: Problem Framing (15 pts) + Tools & Feasibility (15 pts) | Handout 2 + 3*

**Supply Chain Sentinel** is an always-on agentic system that:

1. **Watches:** scans news, weather, ports and supplier signals for disruptions
2. **Connects:** traces the disruption through the supplier graph to the parts at risk
3. **Predicts:** computes a realistic ETA and the financial exposure
4. **Acts:** prepares the lowest-cost fix and escalates costly moves for approval

**Input and context.** Triggers: a scheduled scan, a risk alert, or a planner question. Inputs: external risk feed, supplier graph, shipments, inventory. Context: supplier master and historical lead times.
Dynamic vs static: events, ETAs and stock change constantly; the supplier graph and approval policy stay stable.

---

## 4. Architecture: a supervisor and four specialists
*Rubric: Agentic System Architecture (10 pts) | Handout 5*

```
                 Orchestrator (Supervisor)
        decides which specialist to call and in what order
        |            |             |             |
   RiskIntel   SupplierGraph   ETALogistics   Mitigation
   (perceive)  (trace impact)  (predict ETA)  (score, plan, act)
        |____________|_____________|_____________|
        Tool layer (read / execute / write); each sub-agent runs its own ReAct loop
```

| Pattern | Why we rejected or chose it |
|---|---|
| Single agent, many tools | Rejected: overloaded context, poor decisions (Session 4) |
| Peer-to-peer agents | Rejected: hard to debug, no clear accountability |
| Orchestrator + specialists | Chosen: clear ownership, easy to trace, matches 4 distinct expertises |

---

## 5. Tools: the agent decides, tools execute
*Rubric: Tools, Actions & Feasibility (15 pts) | Handout 3*

| Tool | Type | Approval |
|---|---|---|
| supplier_graph_db, shipment_tracker, inventory_system, external_risk_feed | read | No |
| eta_predictor, risk_scorer | execute | No |
| notify_stakeholders | write | No (reversible) |
| erp_create_po (draft) | write | No (reversible) |
| erp_create_po (commit over limit) | write | Yes |
| expedite_logistics, production_scheduler | write | Yes (costly / live) |

**Decide vs execute:** the agent reasons about WHICH tool to call and with what arguments; the tool just performs the operation. Each tool carries a machine-readable description, an action type and an approval flag. Full descriptions in docs/04.

---

## 6. How the agent thinks: perceive, reason, act, learn
*Rubric: Agentic Thinking and Autonomy (25 pts) | Handout 4*

| Phase | What happens |
|---|---|
| PERCEIVE | RiskIntel scans the external feed and flags high-severity events |
| REASON | SupplierGraph traces each event to the critical parts it threatens |
| PLAN | ETALogistics predicts the real arrival date and the exposure in days and dollars |
| ACT | Mitigation scores the risk, drafts the lowest-cost fix and calls the write tools |
| OBSERVE | Every step is logged to a full audit trail (Langfuse-style tracing) |
| ADAPT | If the first plan is poor, the agent discards it and chooses a better one |

Autonomy with accountability: it acts on its own, but pauses at the moments that matter.

---

## 7. Example run: a live, traceable walkthrough
*Rubric: Agentic Thinking and Autonomy (25 pts) | Handout 7*

- **Trigger:** a typhoon and power cut hit a chip plant in Taiwan.
- **Perceive:** RiskIntel flags the high-severity event from the risk feed.
- **Reason:** SupplierGraph finds the chip is a hidden Tier-2 input to our Stuttgart controllers, a link invisible before.
- **Predict:** the Tier-1 order looks on time but is stuck awaiting that chip; real delay about 19 days against 2 days of stock left, roughly 3 million at risk.
- **Adapt:** it rejects rushing the stuck shipment and switches to a qualified European supplier instead.
- **Act + HITL:** it drafts the PO and pauses for a manager to approve the spend and the schedule change.

**Runs live and offline:** `python run_demo.py --slow` prints the full reasoning trace, both human-approval pauses, and the executive briefing.

---

## 8. Risks, guardrails and human-in-the-loop
*Rubric: Risk Awareness and Mitigation (15 pts) | Handout 6*

| Risk | Guardrail / mitigation |
|---|---|
| Wrong or irreversible action | Costly or live-system writes require human approval |
| Hallucinated disruption | Acts only on confirmed feed data, never on guesses |
| Over-spend | Hard spending limit; orders only to pre-qualified suppliers |
| Prompt injection | External text treated as data, never as commands |
| Stale or missing data | Confidence flags and as-of timestamps on every input |

**Human-in-the-loop points:** committing spend over the limit, booking expedited freight, and changing a live production schedule. Everything else runs autonomously and is fully logged.

---

## 9. Resources and technology stack
*Rubric: Architecture (10 pts) + Feasibility (15 pts) | Handout 8*

| Choice | What | Why |
|---|---|---|
| LLM | Claude (Opus 4.8 reasoning, Haiku for cheap scanning) | Strong tool-use and reasoning; model-agnostic layer lets us swap |
| Cloud | AWS Bedrock / multi-cloud (Bedrock + Vertex) | Keeps data in our own tenant; avoids single-vendor lock-in |
| Language | Python | Richest agent ecosystem; MVP is pure-Python and runs offline |
| Interop | MCP for tools, A2A for agent-to-agent | Open standards so tools and agents stay portable |
| Observability | Langfuse / LangSmith-style tracing | Every decision is logged for audit and debugging |

---

## 10. Benefits and desired outcomes
*Rubric: Problem Framing, measurable value (15 pts) | Handout 1 metrics*

| Today | With the Sentinel |
|---|---|
| Problems found after the line stops | Caught about three weeks earlier |
| Static, unreliable promised dates | Real-time ETA and cost of delay |
| Expensive last-minute freight | Planned, lower-cost fixes |
| Thousands of unsorted alerts | A short, prioritised risk list |

**Target impact:** protect the 14 million dollar quarterly loss, cut expedited freight by about a third, and turn days of analysis into minutes.

---

## 11. Next steps and improvements
*Rubric: Clarity, Presentation Quality & Creativity (20 pts)*

- **Pilot:** run a 3-month pilot on the Stuttgart line; measure stoppage hours and freight cost.
- **Learn:** feed approve/override decisions back so risk scoring improves over time (the learning loop).
- **Scale:** extend to all 28 plants, then to related case challenges such as predictive maintenance and quality.
- **Harden:** add live data connectors (ERP, TMS, news APIs) and full MCP tool servers.

**The ask:** approve a one-line, one-quarter pilot. Low cost, low risk, clearly measurable.

Thank you. We welcome your questions.

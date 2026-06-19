# TEAM REPORT, Supply Chain Sentinel
### Agentic AI for IT · Titan Manufacturing · Challenge #2: Supply Chain Volatility & Risk

This single document is everything the team needs to understand the project, run it, and
present it. It contains:

- **Part A, How the project works** (concept, architecture, code, the demo scenario)
- **Part B, Presentation script** (who says what, slide by slide, ~15 min)
- **Part C, Deliverable to send the instructor** (agent prompts + tool descriptions)
- **Part D, Q&A prep, division of labour, and a pre-flight checklist**

> **Read this first if you have 5 minutes:** we built *Supply Chain Sentinel*, a
> **multi-agent control tower**. A supervisor agent routes work to four specialists that
> **detect** a supply disruption from external signals, **trace** it through the
> multi-tier supplier graph to the critical part it threatens, **predict** the real ETA,
> **score** the risk, and **drive a mitigation plan**, acting autonomously on reversible
> steps and pausing for a human on costly/irreversible ones. It runs as a small Python MVP
> you can demo live (offline, deterministic) with `python run_demo.py --slow`.

---

# PART A, How the project works

## A.1 The problem we chose (in one paragraph)

Titan loses millions to production lines that stop because a part didn't arrive. The root
cause is **fragmented intelligence + manual decision loops**: Titan can't see past its
Tier-1 suppliers, its logistics data is scattered across email/EDI/spreadsheets, and it
has no real-time ETAs, so it discovers a Tier-2 problem only *after* a line has already
stalled. Hard numbers from the case: delivery delays **+28%**, line stoppages **$14M/qtr**,
expedited freight **+52%**.

## A.2 Why an *agent* (and not a script or a chatbot)

| Approach | Why it fails here |
|---|---|
| Rule-based automation / RPA | Can't reason about a *novel* Tier-2 dependency chain it has never seen. |
| A chatbot / single prompt | Can answer questions but can't *act* across ERP/TMS/MES or run a multi-step loop. |
| **Agentic AI** | Perceives scattered signals, **reasons** over a graph, **acts** through tools, and **adapts**, autonomously, 24/7, across 28 plants. |

This is the Session 1-2 progression: a stateless LLM → an **augmented LLM** (LLM + tools +
memory) → **agency** (objective + plan→act→observe→adapt).

## A.3 The architecture (Orchestrator / Supervisor + 4 ReAct sub-agents)

```
                    ORCHESTRATOR (Supervisor)
        owns the objective · routes to specialists · writes the briefing
                                 │
        ┌────────────────┬───────┴────────┬─────────────────────┐
   RiskIntelAgent   SupplierGraphAgent  ETALogisticsAgent   MitigationAgent
   perceive ext.    trace Tier-1→2→3     real-time ETA       score + plan +
   disruptions      to critical parts    (binding constraint) act (with HITL)
        └──────────────── MCP tool layer ────────────────────────┘
              ERP · TMS/EDI · SCADA/Historian · News/Weather APIs
```

- **Why a supervisor (Session 4 trade-off):** one agent with all 10 tools makes poor
  decisions and its context explodes; a peer-to-peer swarm is hard to debug and has no
  clear accountability for a $3M decision. A **supervisor gives clear accountability and is
  simple to debug**, while letting each sub-agent be an expert. Each sub-agent runs the
  **ReAct** loop ("most used, good balance").
- **Memory (Session 2):** in-context (the shared *Blackboard* of this run), external/RAG
  (supplier master, BOM), episodic (past disruptions + what worked), semantic (rules like
  "never expedite a shipment blocked upstream").
- **Interoperability (Session 4):** **MCP** standardises tool/data connectors (keeps
  integrations linear, not N×M); **A2A** = the shared context the agents pass around.
- **Observability (Session 3-4):** every step is traced (the console output *is* the audit
  log; production would stream it to Langfuse/LangSmith).

## A.4 The four use cases (each maps to a case-study issue)

| Use case | Kills which §2 issue | Owning agent |
|---|---|---|
| Tier-N risk mapping | "no visibility beyond Tier-1" | SupplierGraph |
| Real-time ETA prediction | "no real-time ETAs"; delays +28% | ETALogistics |
| Proactive detection & scoring | reactive loops; 22k unprioritised alerts | RiskIntel + risk_scorer |
| Lowest-cost mitigation + HITL | $14M stoppages; freight +52% | Mitigation |

## A.5 The code, file by file

```
mvp/
  run_demo.py              entry point; sets the scenario trigger; CLI flags
  src/
    orchestrator.py        Supervisor: routes to sub-agents, writes the briefing
    agents/
      base.py              BaseAgent + Blackboard (shared A2A context) + HITL helper
      risk_intel_agent.py        PERCEIVE external disruption signals, filter HIGH
      supplier_graph_agent.py    REASON over Tier-1→2→3 deps; find exposed critical parts
      eta_logistics_agent.py     PREDICT real ETA; use the Tier-2 binding constraint
      mitigation_agent.py        SCORE + PLAN + ADAPT + ACT with human-in-the-loop
    tools/
      __init__.py          Tool dataclass + registry (name, description, type, approval)
      data_access.py       READ tools: supplier_graph_db, shipment_tracker,
                           inventory_system, external_risk_feed
      analytics.py         EXECUTE tools: eta_predictor, risk_scorer
      actions.py           WRITE tools: erp_create_po, expedite_logistics,
                           production_scheduler, notify_stakeholders (+ HITL guardrail)
      _data.py             loads the JSON fixtures
    llm.py                 model layer: 'sim' default (offline) or 'claude' (real LLM)
    tracer.py              console observability (PERCEIVE/REASON/PLAN/ACT/OBSERVE/ADAPT)
  data/                    mock SCADA/EDI/ERP/news fixtures (edit these to change the demo)
```

**The golden rule in the code:** *the agent decides, the tool executes.* Every tool is a
passive function with a typed description, an action type (read/write/execute), and a
`requires_approval` flag. The agent classes contain the decisions (which signal matters,
which part is exposed, which mitigation is cheapest, when to escalate).

## A.6 The demo scenario (what actually happens when you run it)

1. **Trigger:** the external feed pushes two HIGH signals, a typhoon suspends Kaohsiung
   port, and **SiliconPath** (a Taiwan chip maker) halts its fab.
2. **RiskIntel** filters those 2 HIGH signals out of the daily noise → affected entities.
3. **SupplierGraph** walks the graph and finds the critical **Servo Motor Controller
   (SVC-2200)**, used on the Stuttgart CNC line, depends on SiliconPath as a
   **single-source Tier-2** input. *This dependency is invisible to Titan today.*
4. **ETALogistics** sees the Tier-1 supplier (Nexa) PO *looks* on-time but is
   `AWAITING_COMPONENTS`; it treats the **Tier-2 chip's ETA (+19 days)** as the binding
   constraint instead of trusting the hollow promised date.
5. **Mitigation** pulls inventory: **runway = 2 days**. `risk_scorer` → **CRITICAL,
   97/100, ~$3.06M exposure**. It first considers expediting the Nexa shipment, then
   **rejects its own plan** (Nexa can't ship without the chip → expediting wastes money)
   and **switches to a qualified EU alternate (AltaControl)** that avoids Taiwan.
6. **Actions:** drafts the buffer PO *autonomously* (reversible), then **pauses for a
   human** to commit the **$294,300** spend and to **reschedule the live line**; notifies
   stakeholders; emits an executive briefing + full audit trace.

## A.7 How to run it

```bash
cd mvp
python3 run_demo.py             # full run, offline & deterministic (no API key)
python3 run_demo.py --slow      # paced output for the live demo
python3 run_demo.py --list-tools     # print the tool catalog (Part C deliverable)
python3 run_demo.py --list-prompts   # print the agent prompts (Part C deliverable)

# Optional: use a real Claude model for the final briefing
pip install anthropic
export ANTHROPIC_API_KEY=...
SENTINEL_LLM=claude python3 run_demo.py
```

No dependencies are needed for the default mode. To change the scenario, edit the JSON in
`mvp/data/` (e.g. raise `daily_consumption` to shorten the runway, or add an event).

## A.8 How it scores against the rubric

| Criterion (pts) | How we earn it |
|---|---|
| Problem Framing, Agent Goals & Prompt (15) | Slides 1-2; measurable goal + metrics; prompts in Part C |
| Agentic System Architecture (10) | Slide 5; supervisor pattern + trade-offs |
| Tools, Actions & Feasibility (15) | Slide 6 + Part C; decide-vs-execute split, realistic tools |
| **Agentic Thinking & Autonomy (25)** | **Slide 7 live demo**; perception→reasoning→action→**adaptation** |
| Risk Awareness & Mitigation (15) | Slide 8; HITL policy, spend caps, injection handling, tracing |
| Clarity, Presentation & Creativity (20) | The deck + the live, narrated agent loop |

---

# PART B - Presentation script (about 15 minutes, board audience)

> The deck is a business pitch to Titan's board. Keep the language plain, lead with money
> and risk, and let the live example (slide 7) carry the weight. Times are targets. Assign
> one speaker per block. No em-dashes anywhere, on the slides or in speech.

**[Slide 0, Title] (0:00 to 0:30), Speaker 1**
> "Good morning. Last quarter, Titan lost 14 million dollars to production lines that
> stopped because a part did not arrive, and we found out too late. We are Team [X], and we
> are proposing an AI teammate we call Supply Chain Sentinel. It protects our production
> lines by catching supply problems weeks earlier than we can today."

**[Slide 1, Why our lines keep stopping] (0:30 to 2:00), Speaker 1**
> "Our output is down 9% this year and we keep missing customer deadlines. The cause sits
> in our supply chain. On the left is what we see: suppliers deliver late 28% more often,
> missing parts cost us 14 million dollars last quarter, and emergency shipping is up 52%.
> On the right is why it keeps happening. We can see our direct suppliers, but not the
> companies that supply them. Our shipping information is scattered across emails and
> spreadsheets. And we still trust the original promised dates even when they are already
> wrong. In short, we react too late because our information is scattered and our decisions
> are manual."

**[Slide 2, The opportunity] (2:00 to 3:00), Speaker 1**
> "Today our teams chase this by hand, one problem at a time, and usually too late. We need
> something that watches every warning signal day and night and acts before a line stops.
> Our goal is simple: keep every critical part in stock by spotting risk early and fixing
> it at the lowest cost, with our managers approving the important decisions. We will know
> it works when warnings arrive in minutes instead of days, when we catch most problems
> before a delivery is even late, and when emergency shipping falls by about a third."

**[Slide 3, A 24/7 guardian] (3:00 to 3:45), Speaker 2**
> "So we propose a digital assistant that never sleeps and does four things. It watches the
> news, weather, ports and supplier updates. It connects the dots, mapping which of our
> products depend on a troubled supplier, even two or three steps up the chain. It predicts
> when parts will really arrive and how much money is at risk. And it acts, preparing the
> fix and asking a manager to approve the costly moves. Today those four jobs are split
> across teams who do not share information. This puts them in one place."

**[Slide 4, It fixes our exact problems] (3:45 to 4:30), Speaker 2**
> "Every problem from the first slide has a fix here. We cannot see past our direct
> suppliers, so it maps the full chain. Our promised dates are unreliable, so it predicts
> the real arrival date and the cost. We drown in alerts, so it ranks them. And our
> reactions are slow and expensive, so it prepares the lowest-cost fix in minutes. One
> assistant covers the whole challenge."

**[Slide 5, How it works] (4:30 to 5:45), Speaker 2**
> "In plain terms, think of it as a small team of four AI specialists led by a supervisor.
> A Watcher spots disruptions in the outside world. A Mapper traces them to the parts at
> risk. A Forecaster predicts arrival dates and cost. A Planner prepares the fix. The
> supervisor decides which specialist to use and combines their findings into one
> recommendation. Why a team and not one big system? Because a single all-in-one tool tries
> to do too much and makes poor decisions, while four focused specialists are more accurate
> and far easier to check and trust. It runs on proven, secure AI, hosted in our own cloud,
> so our data stays protected."

**[Slide 6, Who stays in control] (5:45 to 6:45), Speaker 3**
> "This is the part that matters most for trust. On its own, the Sentinel only does
> low-risk, reversible things: it reads our systems, calculates the risk, drafts a
> recommendation and sends alerts. For anything costly or hard to undo, a manager must
> approve: committing real spend, paying for emergency freight, or changing a live
> production schedule. Nothing irreversible ever happens without a person signing off, and
> every step is recorded."

**[Slide 7, A real example, with the live demo] (6:45 to 10:30), Speaker 3 drives, Speaker 1 narrates**
> "Let me show you a real example. (Start the live demo, or walk the slide.)
> A typhoon and a power cut hit a chip factory in Taiwan. The Sentinel finds that a chip
> from that factory is essential for the controllers on our Stuttgart line, a link we could
> not see before. Our supplier's order looks on time, but it is actually stuck waiting for
> that chip, about 19 days late. We have only 2 days of stock left, so the risk is around 3
> million dollars. Here is the clever part: the Sentinel does not waste money rushing a
> shipment that is already stuck. It switches to an approved European supplier instead. Then
> it prepares the order and asks a manager to approve the 294,000 dollar spend and the
> schedule change. The result is a 3 million dollar problem caught three weeks early, with a
> plan ready to go."

**[Slide 8, Keeping it safe] (10:30 to 11:30), Speaker 1**
> "We know the board cares about risk, so let us be direct. People approve every costly or
> irreversible action, and the AI never spends on its own. Spending limits are built in, and
> orders can only go to suppliers we have already approved. It acts only on confirmed
> information, never on rumours. It treats outside information as data, never as commands,
> so it cannot be tricked. And every decision is recorded for compliance. The AI supports
> our teams, it does not replace them."

**[Slide 9, What we gain] (11:30 to 12:15), Speaker 2**
> "The before and after is clear. We move from finding problems after a line stops to
> catching them three weeks earlier. From outdated promised dates to the real arrival date
> and cost. From expensive emergency shipping to planned, lower-cost fixes. From thousands
> of unsorted alerts to a short, prioritised list. Our target is to protect that 14 million
> dollar quarterly loss, cut emergency shipping by about a third, and turn days of analysis
> into minutes."

**[Slide 10, Our recommendation] (12:15 to 13:15), Speaker 3**
> "Our recommendation is a three-month pilot on the Stuttgart line. We measure two clear
> numbers: hours of line stoppage and emergency shipping cost. If it works, we scale it to
> our other plants and to related challenges like machine maintenance and quality. The ask
> is simple: approve a one-line, one-quarter pilot. It is low cost, low risk and clearly
> measurable. Thank you, and we welcome your questions."

**[Q&A] (13:15 to 15:00), all** (see Part D).



# PART C, DELIVERABLE: Agent Prompts & Tool Descriptions

> *Send this section to the instructor before the presentation (required). It is generated
> from the live code, regenerate with `python run_demo.py --list-prompts` and
> `--list-tools`.*

## C.1 Agent system prompts (active, agents make decisions)

**Orchestrator, SupplyChainSentinel**
> You are the Supply Chain Sentinel supervisor for Titan Manufacturing. You own the
> objective of protecting critical-part availability across 28 plants. You do not call data
> tools directly; you DECIDE which specialist sub-agent to invoke and in what order:
> RiskIntel (perceive external signals) → SupplierGraph (trace Tier-2/3 impact to critical
> parts) → ETALogistics (predict realistic availability) → Mitigation (score + plan + act
> with human-in-the-loop). Then synthesize a single executive briefing. Route only what is
> needed, keep a clear audit trail, and ensure no irreversible action is taken without
> human approval.

**RiskIntelAgent**
> You are the Risk Intelligence agent for Titan Manufacturing's supply chain control tower.
> Your job is to continuously scan external signals (weather, port status, supplier news,
> geopolitical/export events) and identify which suppliers, ports or regions are disrupted.
> Output a concise list of affected entities with severity. Do NOT decide mitigations, 
> only surface validated signals. Never invent events: rely strictly on the
> external_risk_feed tool. If a signal is ambiguous, mark confidence low rather than
> over-claiming.

**SupplierGraphAgent**
> You are the Supplier Graph agent. Given one or more disrupted upstream entities, use the
> supplier_graph_db tool to determine which Tier-1 suppliers and which CRITICAL PARTS depend
> on them, i.e. give Titan visibility BEYOND Tier-1. For each impacted critical part,
> report the binding upstream constraint, whether it is single-sourced, and any qualified
> alternate supplier. Reason explicitly about dependency chains; do not assume a Tier-1
> 'on-time' status is safe if its Tier-2 input is disrupted.

**ETALogisticsAgent**
> You are the ETA & Logistics agent. For each impacted critical part, locate the relevant
> in-transit shipments via shipment_tracker (consolidating EDI, email and carrier
> spreadsheets) and call eta_predictor to produce a realistic ETA and delay. Crucially, if
> a Tier-1 shipment is blocked on a disrupted Tier-2 input, treat the Tier-2 component's ETA
> as the binding constraint, do not trust the Tier-1 promised date. Output the predicted
> availability date and the dominant delay driver.

**MitigationAgent**
> You are the Mitigation Planner for Titan's supply chain. For each impacted critical part
> you receive inventory runway and a predicted availability date. Steps: (1) call
> risk_scorer to prioritize; (2) for HIGH/CRITICAL risk, design the LOWEST-COST mitigation
> that restores availability before stockout, preferring options that avoid the disrupted
> route; (3) DO NOT expedite a shipment that is blocked on a disrupted upstream input, 
> that wastes premium freight; (4) you MAY autonomously draft POs and send notifications
> (reversible), but you MUST escalate to a human for: committing spend over policy limit,
> booking expedited freight, or changing a live production schedule. Always present the cost
> trade-off and your recommendation.

## C.2 Tool descriptions (passive, tools perform actions)

**READ**
- **supplier_graph_db** *(read; no approval; read-only on Supplier Master / SRM graph)*, 
  Query Titan's multi-tier supplier graph. Given a part number returns the full Tier-1→2→3
  dependency chain, qualified alternate suppliers, single-source flags, country/region and
  lead times. Use to gain visibility beyond Tier-1 and trace which upstream supplier feeds a
  critical part.
- **shipment_tracker** *(read; no approval; read-only on TMS / EDI gateway)*, Consolidated
  in-transit shipment status from the otherwise fragmented sources (EDI 856 ASN feeds,
  supplier emails, carrier spreadsheets). Returns origin, carrier, promised ETA, last-known
  status and notes. Use to check whether an open order is actually moving.
- **inventory_system** *(read; no approval; read-only on ERP inventory)*, On-hand units,
  safety stock, daily consumption and any open PO for a part at a plant, and computes the
  inventory runway (days of cover before the line stops). Use to quantify urgency and
  stoppage cost.
- **external_risk_feed** *(read; no approval; read-only on news/weather/port APIs + web
  search)*, Scan external disruption signals (weather, port status, supplier news,
  geopolitical/export-control). Filterable by region or supplier. Use to detect upstream
  risk proactively, before a Tier-1 delay or stall appears.

**EXECUTE**
- **eta_predictor** *(execute; no approval; stateless compute)*, Predict a realistic ETA
  for an in-transit shipment by combining promised ETA, last-known status and active
  disruption signals. Returns predicted_eta, delay days, confidence and a human-readable
  explanation. Replaces static promised dates with a real-time ETA.
- **risk_scorer** *(execute; no approval; stateless compute)*, Compute a 0-100 risk score
  and band (LOW/MEDIUM/HIGH/CRITICAL) from runway, predicted delay, single-source status and
  line-stoppage cost. Returns exposure days and exposure $. Use to prioritize which risks
  deserve action.

**WRITE**
- **erp_create_po** *(write; **commit/over-limit needs human approval**; write to ERP
  Procurement, qualified suppliers only)*, Create a PO (draft or commit). Drafts are
  reversible (autonomous); a COMMIT or any spend over the policy limit auto-escalates for
  approval via an approval token. Use to secure buffer stock or switch to a qualified
  alternate.
- **expedite_logistics** *(write; **always needs human approval**; write to TMS,
  budget-controlled)*, Book premium/expedited freight to recover transit time. Always needs
  approval (controlled cost, +52% trend). Use only when runway < standard lead time.
- **production_scheduler** *(write; **always needs human approval**; write to MES,
  plant-scoped)*, Propose a live production-line schedule change. Touches OT/operators/
  safety → always needs plant-planner approval. Use to buy time when materials arrive late.
- **notify_stakeholders** *(write; no approval; send-only on notification channel)*, Send a
  structured alert/briefing to procurement / plant planner / control tower via email or
  Teams/Slack. Reversible, so the agent may send autonomously.

## C.3 The decision / action split (the rubric line)

- **The AGENT decides:** which signals matter, which critical parts are exposed, what the
  binding constraint is, whether risk warrants action, which mitigation is cheapest, and
  *not* to expedite a blocked shipment.
- **The TOOLS execute:** query a database, compute an ETA/score, draft/commit a PO, book
  freight, reschedule a line, send a message. No tool ever decides on its own.

---

# PART D, Q&A prep, roles, and pre-flight checklist

## D.1 Likely questions & crisp answers

- **"Is this real AI or scripted?"** The MVP reasoning is rule-based so the demo is
  reproducible offline, but the design is model-ready: `llm.py` swaps in Claude with one
  env var, and in production each sub-agent's ReAct loop is LLM-driven over the same typed
  tool catalog. The architecture, tool contracts and guardrails are exactly what a real
  LangGraph/Helix build uses.
- **"Why Claude / which model?"** Strong tool-use + multi-step reasoning, large context for
  graphs/telemetry, available on Bedrock and Vertex (suits Titan's multi-cloud, OT-sensitive
  setup). We'd pair a generic LLM for orchestration with an optional fine-tuned model for
  numeric ETA/RUL (Session 7).
- **"What if the agent is wrong?"** Reversible actions only run autonomously; every costly
  or irreversible action pauses for a human, a spend cap auto-escalates, and the full trace
  is an audit log. Worst realistic case is a wasted draft PO that a human declines.
- **"How does it learn?"** Not for free (Session 2 myth), planner approvals/edits become
  episodic feedback that tunes risk thresholds and supplier preferences over time.
- **"Why multi-agent and not one agent?"** One agent with 10 tools makes poor decisions and
  its context explodes; a supervisor gives accountability and is debuggable.
- **"How is this different from existing supply-chain software?"** Those tools *show*
  dashboards; the agent *reasons and acts* across them, end-to-end, and proactively traces
  Tier-2/3 risk that today is invisible.

## D.2 Suggested division of labour (adapt to your group size)

| Person | Owns | Slides |
|---|---|---|
| Speaker 1 | Problem + goals + risk narrative | 0, 1, 2, 8 |
| Speaker 2 | Solution + architecture + benefits | 3, 4, 5, 9 |
| Speaker 3 | Tools + **runs the live demo** + next steps | 6, 7, 10 |

(For a 2-person group, merge Speaker 2 and 3; the demo-driver also covers architecture.)

## D.3 Pre-flight checklist (before you present)

- [ ] Replace **[teammate]** placeholders on the title slide (`presentation/build_pptx.py`,
      then re-run it) and in this report.
- [ ] Send **Part C** (prompts + tool descriptions) to the instructor *before* the talk.
- [ ] On the demo laptop: `cd mvp && python3 run_demo.py --slow` works (Python 3.9+; no
      internet needed).
- [ ] Have a **fallback**: a screen-recording or the captured trace in `docs/05_demo_flow.md`
      in case live execution fails.
- [ ] Decide who clicks vs who talks during the demo (Speaker 3 clicks, Speaker 1 narrates).
- [ ] Rehearse once with a timer, target 13-14 min so there's room for Q&A.
- [ ] Bring the deck as **.pptx** (`presentation/Supply_Chain_Sentinel.pptx`) *and* export a
      PDF backup.

## D.4 Where everything lives

| Artifact | Path |
|---|---|
| Slides (PowerPoint) | `presentation/Supply_Chain_Sentinel.pptx` |
| Slides (source / regenerate) | `presentation/build_pptx.py`, `presentation/Supply_Chain_Sentinel.md` |
| This report | `docs/TEAM_REPORT.md` |
| Prompts + tools deliverable | this report Part C, or `docs/04_agent_prompts_and_tools.md` |
| Design-handout answers (§1-8) | `docs/02_solution_design.md` |
| Architecture detail | `docs/03_architecture.md` |
| Demo script + expected output | `docs/05_demo_flow.md` |
| Risk register | `docs/06_risks_and_mitigations.md` |
| Runnable MVP | `mvp/` (`python3 run_demo.py`) |

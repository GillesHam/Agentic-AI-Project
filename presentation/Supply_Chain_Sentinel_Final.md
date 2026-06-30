---
marp: true
theme: default
size: 16:9
paginate: true
---

<!--
Supply Chain Sentinel, FINAL deck. Same design as the third deck
(Supply_Chain_Sentinel_Design.md), but with warmer, more fluent language, no
abbreviations except the obvious ones (AI, IT), and exactly 10 content slides plus a
title slide and a thank-you slide. No em-dashes.
Source of truth for the .pptx is build_pptx_final.py.
-->

# Supply Chain Sentinel
### An agentic AI teammate that keeps our production lines running through supply shocks
Designed for Titan Manufacturing Corporation

Agentic AI for IT | IE University, School of Science and Technology
Team: Gilles Hamers, [teammate], [teammate]

---

## 1. What the agent is for, and why it matters
*Rubric: problem framing, agent goals and prompt (15 points) | Design handout, section 1*

**Our goal:** keep every critical part available at every plant. The agent spots a supply risk early, before it can stop a production line, then arranges the most affordable fix, while always asking a person to approve anything expensive or hard to undo.

**Why this matters to the business**
- When a line stops it is painful: stoppages cost us $14 million last quarter, and a single critical machining line loses around $180,000 for every day it sits idle.
- By noticing trouble two suppliers deep and roughly a week sooner, we can replace costly last-minute air freight (already up by more than half) with calm, planned orders that also protect our delivery promises.

**How we will know it is working**
- The time from first warning to a clear decision falls from days to minutes.
- We catch at least seven in ten disruptions before a direct supplier is even visibly late.
- Rushed-freight spending drops by about a third, with every critical part mapped down to its deepest suppliers.

---

## 2. What the agent observes and remembers
*Rubric: problem framing (15 points) and architecture (10 points) | Design handout, section 2*

| | How it works |
|---|---|
| What wakes it up | A risk alert that arrives on its own, a routine check every fifteen minutes, or a planner simply asking a question. |
| What it reads | Outside risk signals, electronic shipping notices, supplier emails, carrier spreadsheets, live inventory and open orders, the supplier map, and the parts list (the Bill of Materials). |
| What moves and what stays steady | Always moving: shipment status, arrival dates, stock levels, events and prices. Mostly steady: the supplier map, the parts list, approved suppliers and approval rules. |

**The four kinds of memory it draws on**

| Working memory | Reference knowledge | Past experience | General know-how |
|---|---|---|---|
| Shared notes for the case in hand | Supplier records, parts lists, contracts and approved alternates | Earlier disruptions and the fixes that worked | Rules of thumb and domain knowledge |

---

## 3. One supervisor guiding four specialists
*Rubric: agentic system architecture (10 points) | Design handout, section 5*

```
Triggers (an alert, a regular check, or a planner's question)
                          |
              THE SUPERVISOR  -- sets the goal, decides who works on
                          |     what, and writes the final briefing;
   Shared notes pass between the agents, each running a reason-and-act loop
   |                  |                    |                  |
Risk Intelligence  Supplier Mapping   Arrival Forecast   Mitigation
(watches)          (traces chain)     (predicts arrival) (plans and acts)
   |                  |                    |                  |
========= Tools the agents call (a star = needs human approval) =========
Risk feed       Supplier map        Shipment tracker   Create purchase order *
                Inventory           Arrival predictor  Expedite freight *
                                    Risk scorer        Reschedule line *
                                                       Notify people
Connects to our real systems: the planning system, transport and shipping data,
factory-floor controls, the manufacturing system, and news and weather feeds.
```

---

## 4. Why we chose a supervisor over the alternatives
*Rubric: agentic system architecture (10 points) | Design handout, section 5*

| The option | Verdict | The reason |
|---|---|---|
| One agent holding every tool | Not chosen | Too many tools lead to poor choices, the context grows unmanageable, and one agent cannot be expert at everything. |
| Independent agents talking peer to peer | Not chosen | Hard to predict and to debug, with no clear accountability for a three-million-dollar decision. |
| A supervisor guiding specialists | Our choice | Clear accountability, easy to follow and fix, work shared among experts, every step auditable. |
| A deeper management hierarchy | For later | More than we need today, but a natural way to grow as we take on the other challenges. |

**The trade-off we accept:** a few more moving parts and a little extra coordination, which we keep in check with a light supervisor and tightly limited tools. A simple automation script could never reason about a brand-new supplier chain, or sensibly decide not to rush a shipment.

---

## 5. The agent decides, the tools carry out the work
*Rubric: tools, actions and feasibility (15 points) | Design handout, section 3*

Each tool is passive and does one job when asked. The agent is the one that decides which tool to use, and when.

| Tool | Kind | Needs approval | What it does |
|---|---|---|---|
| Supplier map | read | no | Traces dependencies through every supplier tier and finds approved alternates |
| Shipment tracker | read | no | Brings scattered shipping updates into a single, clear view |
| Inventory | read | no | Shows stock on hand, safety stock and days of cover left |
| Risk feed | read | no | Scans weather, ports, news and geopolitical signals |
| Arrival predictor | calculate | no | Estimates a realistic arrival date from status and live disruptions |
| Risk scorer | calculate | no | Turns the picture into a 0 to 100 priority score and a dollar exposure |
| Create purchase order | act | to commit funds | Drafts an order freely; committing real money needs a person |
| Expedite freight | act | always | Books premium shipping, which is a controlled cost |
| Reschedule line | act | always | Reorders a live production line, which affects people and safety |
| Notify people | act | no | Sends an alert or briefing, which is easily reversible |

---

## 6. How the agent thinks: notice, reason, act, learn
*Rubric: agentic thinking and autonomy (25 points) | Design handout, section 4*

- **Notice:** the Risk Intelligence specialist sifts the serious signals out of the daily noise (the case describes around 22,000 unsorted alerts a day).
- **Reason:** the Supplier Mapping specialist follows the chain to the critical parts a troubled supplier feeds, and treats a stuck part upstream as the real bottleneck rather than trusting an optimistic promised date.
- **Act:** it drafts a backup order on its own, then, once a person signs off, places the order, reschedules the line, tells the right people, and records everything.
- **Learn:** every run is remembered, and the approvals and edits planners make become feedback that gradually tunes the risk thresholds and supplier preferences.

An honest note: these agents do not improve by magic. They get better because we feed real human feedback back into them.

---

## 7. A real example: a major risk caught early
*Rubric: agentic thinking and autonomy (25 points) | Design handout, section 7*

- **The trigger:** the risk feed reports a typhoon closing the port of Kaohsiung and a power failure halting a chip factory in Taiwan.
- **Tracing it:** the agent flags both as serious, then finds that our critical Servo Motor Controller (part SVC-2200) quietly depends on that single Taiwanese chip supplier, two tiers up, through our direct supplier Nexa.
- **Predicting:** it sees that Nexa's order is really stuck waiting for that chip, so the true delay is about 19 days, while we hold only 2 days of stock.
- **Scoring:** the risk comes back critical, 97 out of 100, with roughly $3.06 million at stake.
- **Adapting:** the agent first considers rushing Nexa's shipment, then rejects that idea, because Nexa cannot ship without the missing chip, and instead switches to an approved European supplier, AltaControl, that avoids Taiwan altogether.
- **Acting, with a person:** it drafts the backup order on its own, then asks a manager to approve the $294,300 commitment and the line change, and notifies everyone involved.

**The result:** a critical risk caught around three weeks before the line would have stopped, with a costed plan ready and a complete record of every step. We can run this live.

---

## 8. What could go wrong, and how we prevent it
*Rubric: risk awareness and mitigation (15 points) | Design handout, section 6*

| What could go wrong | How we prevent it |
|---|---|
| A wrong or irreversible action | Actions begin as drafts; anything costly or live needs a person to sign off. |
| An invented or imagined event | The risk specialist must point to a real signal in the feed; it may never guess. |
| Spending too much | A firm spending limit escalates large commitments, and orders go only to approved suppliers. |
| One agent's mistake spreading | A light supervisor, tightly limited tools, and a full trace of every step keep errors contained. |
| Hidden instructions inside supplier messages | Outside text is always treated as information to read, never as commands to follow. |

**A person stays in the loop** for the decisions that matter: committing money beyond the limit, booking premium freight, or changing a live production schedule. Everything that is easily reversible runs on its own.

---

## 9. How it is built and how it connects
*Rubric: architecture (10 points) and feasibility (15 points) | Design handout, section 8*

We chose proven, open technology, so the system stays flexible, secure and easy to inspect.

| Choice | What we use | Why |
|---|---|---|
| Reasoning | Claude (the Opus or Sonnet model) as the thinking engine | Excellent at using tools and reasoning over many steps, with room for large context |
| Specialist forecasts | The option to add a purpose-trained model for arrival and lifespan predictions | Purpose-trained models do better on numeric forecasts, and we can swap models freely |
| Hosting | Managed services on Amazon Bedrock or Google Vertex | Keeps our data in our own environment, with no heavy hardware to run ourselves |
| Building blocks | Python, with established agent frameworks (or a no-code option) | The richest ecosystem for agents, and our prototype runs offline in plain Python |
| Connections and tracing | The Model Context Protocol, Agent-to-Agent messaging, and tracing tools | Keeps integrations simple and makes every decision fully auditable |

Our working prototype already mirrors this design: a model layer stands in for Claude, a tool registry for the connectors, a console trace for the production tracing, and a single orchestrator for the supervisor.

---

## 10. The payoff, and where we go next
*Rubric: clarity, presentation quality and creativity (20 points) | Assignment: benefits and next steps*

**What we expect to gain**
- Protect that $14 million quarterly loss and cut rushed-freight spending by roughly a third.
- Turn days of manual analysis into minutes, with full visibility into every critical part, right down to its deepest suppliers.

**Where we go next**
- **Pilot:** run a three-month trial on the Stuttgart line and measure two things, hours of downtime and freight cost.
- **Learn:** feed planner approvals and edits back in to sharpen the risk scores and supplier preferences.
- **Grow:** extend it to all twenty-eight plants, and then to the other challenges such as maintenance and quality, using the deeper hierarchy described earlier.
- **Strengthen:** connect the live systems and add full production-grade tracing.

**What we are asking for:** approval to run a single-line, single-quarter pilot. Low cost, low risk, and easy to measure.

---

# Thank you
### We would love to hear your questions.

Supply Chain Sentinel: catching supply shocks early, and keeping Titan's lines running.

Team: Gilles Hamers, [teammate], [teammate] | Agentic AI for IT, IE University

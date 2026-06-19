---
marp: true
theme: default
paginate: true
size: 16:9
header: 'A Proposal to the Board of Titan Manufacturing'
footer: 'Supply Chain Sentinel'
style: |
  section { font-size: 25px; }
  h1 { color: #0a1f6b; }
  h2 { color: #0a1f6b; }
  strong { color: #6CB400; }
  table { font-size: 20px; }
---

<!--
This is the board-level deck in Marp markdown, kept in sync with the canonical PowerPoint
(Supply_Chain_Sentinel.pptx, built by build_pptx.py). Audience: Titan's board. Plain
business language, no em-dashes. Speaker notes are in HTML comments under each slide.
-->

# Supply Chain Sentinel
## An AI teammate that protects our production lines from supply shocks

A proposal to the Board of Titan Manufacturing Corporation

Agentic AI for IT | IE University · Team: Gilles Hamers, [teammate], [teammate]

<!-- Opening (30s): Last quarter we lost 14 million dollars to lines that stopped because a
part did not arrive, and we found out too late. We propose an AI teammate that catches this
weeks earlier. -->

---

## 1. Why our production lines keep stopping

Our output is down **9% this year** and we keep missing customer deadlines. The cause is our supply chain.

| What we are seeing | Why it keeps happening |
|---|---|
| Suppliers deliver late **28% more often** | We see our direct suppliers, but not who supplies them |
| Missing parts stopped our lines: **14M dollars last quarter** | Shipping data is scattered across emails, spreadsheets and separate systems |
| We find a supplier problem **only after a line stops** | We trust original promised dates, even when they are already wrong |
| Emergency shipping costs are **up 52%** | Every decision is made by hand, after the problem has hit |

**In short: we react too late because our information is scattered and our decisions are manual.**

<!-- (90s) Left column is the pain, right column is the root cause. -->

---

## 2. The opportunity

- Today our teams chase this information across many systems, one problem at a time, and usually too late.
- We need something that watches every warning signal, day and night, and acts before a line stops.

**Our goal:** keep every critical part in stock by spotting supply risk early and fixing it at the lowest cost, with our managers approving the important decisions.

**How we measure success:** warnings in minutes not days · most disruptions caught before a delivery is even late · emergency shipping down about a third.

<!-- (60s) Business framing. The metrics make the promise concrete. -->

---

## 3. A 24/7 supply chain guardian

We propose **Supply Chain Sentinel**, a digital assistant that never sleeps and does four things:

1. **Watches:** scans news, weather, ports and supplier updates for anything that could disrupt us.
2. **Connects the dots:** maps which of our products depend on a troubled supplier, even two or three steps up the chain.
3. **Predicts:** works out when parts will really arrive and how much money is at risk.
4. **Acts:** prepares the fix (reorder, switch supplier, adjust the schedule) and asks a manager to approve the costly moves.

<!-- (45s) One assistant doing work split today across several teams who do not share data. -->

---

## 4. It fixes the exact problems we have

| Our problem today | How the Sentinel fixes it |
|---|---|
| We cannot see past our direct suppliers | Maps the full chain and flags hidden risks early |
| Promised delivery dates are unreliable | Predicts the real arrival date and the cost of delay |
| Too many alerts, no way to prioritise | Ranks the risks so we focus on what truly matters |
| Slow, manual, expensive reactions | Prepares the lowest-cost fix in minutes, ready for approval |

**One assistant that covers every part of this challenge.**

<!-- (45s) Pre-answers: does it actually address our problem? Yes. -->

---

## 5. How it works, in plain terms

Think of it as a small team of four AI specialists, led by a supervisor:

- **Watcher:** spots disruptions in the outside world
- **Mapper:** traces them to the parts at risk
- **Forecaster:** predicts real arrival dates and cost
- **Planner:** prepares the fix and flags approvals

The supervisor decides which specialist to use and combines their findings into one clear recommendation.

**Why a team and not one big system?** A single all-in-one tool tries to do too much and makes poor decisions. Four focused specialists are more accurate and far easier to check and trust. Built on proven, secure AI and hosted in our own cloud, so our data stays protected.

<!-- (75s) Keep it non-technical. If pressed: agents + orchestrator on Claude in our cloud. -->

---

## 6. The AI assists. Our people decide.

**The Sentinel does on its own** (low risk, easy to undo):
read our systems · calculate the risk · draft a recommendation · send alerts.

**A manager must approve** (high cost or hard to undo):
commit real spend · pay for emergency freight · change a live production schedule.

**Nothing irreversible ever happens without a person signing off, and every step is recorded for full transparency.**

<!-- (60s) The trust slide. AI prepares and recommends; people own the money decisions. -->

---

## 7. A real example

- A typhoon and a power cut hit a chip factory in Taiwan.
- The Sentinel finds that a chip from that factory is essential for the controllers on our Stuttgart line, a link we could not see before.
- Our supplier's order looks on time, but is actually stuck waiting for that chip. The real delay is about **19 days**.
- We have only **2 days of stock** left. If the line stops, the risk is about **3 million dollars**.
- The Sentinel does not waste money rushing a shipment that is already stuck. It switches to an approved **European supplier** instead.
- It prepares the order and asks a manager to approve the **294,000 dollar** spend and the schedule change.

**Result: a 3 million dollar problem caught three weeks early, with a plan ready to go.** (We can show this running live.)

<!-- (3-4 min) Optionally run the live demo. Key moment: the Sentinel rejects its own first
idea and finds a smarter, cheaper fix. That is real reasoning, not a fixed script. -->

---

## 8. Keeping it safe and trustworthy

- **People approve every costly or irreversible action.** The AI never spends on its own.
- **Spending limits are built in,** and orders can only go to suppliers we already approved.
- **It acts only on confirmed information,** never on guesses or rumours.
- **Outside information is treated as data, never as commands,** so the system cannot be tricked.
- **Every decision is recorded,** giving us a complete audit trail for compliance.

**The AI supports our teams. It does not replace them.**

<!-- (60s) Risk is a board concern, meet it head on. Aside for the professor: the handout
PDF itself contained a hidden manipulation attempt; the system treats such text as data. -->

---

## 9. What we gain

| Today | With the Sentinel |
|---|---|
| We find supplier problems after the line stops | We catch them about three weeks earlier |
| We rely on outdated promised dates | We know the real arrival date and the cost |
| Expensive, last-minute emergency shipping | Planned, lower-cost fixes |
| Thousands of unsorted alerts | A short, prioritised list of real risks |

**Target: protect the 14 million dollar quarterly loss, cut emergency shipping by about a third, and turn days of analysis into minutes.**

<!-- (45s) The so-what slide. Tie each benefit to money and customer deadlines. -->

---

## 10. Our recommendation

- **Run a 3-month pilot** on the Stuttgart production line.
- **Measure two clear numbers:** hours of line stoppage and emergency shipping cost.
- **If it works, scale it** to our other plants and to related challenges such as machine maintenance and quality.

**The ask: approve a one-line, one-quarter pilot. Low cost, low risk, clearly measurable.**

Thank you. We welcome your questions.

<!-- (45s) End on the pilot ask, then take questions. -->

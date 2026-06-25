# Supply Chain Sentinel, Agentic AI for Titan Manufacturing

**Course:** Agentic AI for IT (IE University, School of Science & Technology)
**Case study:** Titan Manufacturing Corporation, Challenge #2, *Supply Chain Volatility & Risk*
**Team deliverable:** final assignment (presentation + MVP + design)

---

## What this is

**Supply Chain Sentinel** is a multi-agent system that gives Titan a 24/7 *supply-chain
control tower*. It detects supply-chain risk **before** it stops a production line,
traces it through the **multi-tier supplier graph** (visibility beyond Tier-1), predicts
**real-time ETAs** from fragmented logistics data, scores and prioritizes the risk, and
then **drives the lowest-cost mitigation**, taking reversible actions autonomously and
escalating costly/irreversible ones to a human.

It directly attacks every symptom and underlying issue listed under *§2 Supply Chain
Volatility & Risk* in the case study (see [docs/01_problem_statement.md](docs/01_problem_statement.md)).

## Repository layout

```
.
├── README.md                      ← you are here
├── docs/                          ← the written design (maps 1:1 to the rubric + handout)
│   ├── TEAM_REPORT.md             ← ★ START HERE: how it works + presentation script + deliverable
│   ├── 01_problem_statement.md
│   ├── 02_solution_design.md      ← Design-Thinking handout, sections 1-8 answered
│   ├── 03_architecture.md         ← architecture + diagrams + trade-offs
│   ├── 04_agent_prompts_and_tools.md   ← DELIVERABLE to send before the presentation
│   ├── 05_demo_flow.md            ← exact demo script + expected output
│   └── 06_risks_and_mitigations.md
├── presentation/                  ← three deck versions (each .pptx + Marp .md + build script)
│   ├── Supply_Chain_Sentinel.*            ← v1: board-level business pitch
│   ├── Supply_Chain_Sentinel_Technical.*  ← v2: business + technical hybrid (rubric-tagged)
│   └── Supply_Chain_Sentinel_Design.*     ← v3: technical design / architecture deep dive
├── mvp/                           ← runnable MVP (pure Python, no API key needed)
│   ├── run_demo.py                ← CLI demo
│   ├── streamlit_app.py           ← ★ interactive demo dashboard (live HITL, graph, KPIs)
│   ├── sentinel_runtime.py        ← bridge that runs the real agents and captures the trace
│   ├── requirements.txt / app_requirements.txt
│   ├── src/                       ← orchestrator, 4 sub-agents, tools, LLM layer, tracer
│   └── data/                      ← mock SCADA/EDI/ERP/news datasets
└── (original PDFs: assignment, handout, case study)
```

## Run the MVP (30 seconds)

```bash
cd mvp
python3 run_demo.py             # full agentic run, offline & deterministic
python3 run_demo.py --slow      # paced for a live presentation
python3 run_demo.py --list-tools     # print the tool catalog (a graded deliverable)
python3 run_demo.py --list-prompts   # print every agent's system prompt
```

No dependencies are required for the default (`sim`) mode, it runs on the Python
standard library. To use a real Claude model for the final briefing:

```bash
pip install anthropic
export ANTHROPIC_API_KEY=...    # your key
SENTINEL_LLM=claude python3 run_demo.py
```

## Interactive demo dashboard

For the live presentation there is a Streamlit dashboard that drives the same agents and
lets the audience watch them work, with real **Approve / Reject** buttons at each
human-in-the-loop checkpoint, KPI cards, and a supplier graph that highlights the
disruption:

```bash
cd mvp
pip install -r app_requirements.txt
streamlit run streamlit_app.py
```

## How it maps to the grading rubric

| Rubric criterion (points) | Where to find it |
|---|---|
| Problem Framing, Agent Goals & Prompt (15) | docs/01, docs/02 §1, docs/04 |
| Agentic System Architecture (10) | docs/03, slide 5 |
| Tools, Actions & Feasibility (15) | docs/04, `--list-tools`, slide 6 |
| Agentic Thinking & Autonomy (25) | the live MVP trace, docs/05, slide 7 |
| Risk Awareness & Mitigation (15) | docs/06, slide 8, HITL guardrails in code |
| Clarity, Presentation & Creativity (20) | presentation/ deck |

## A note on academic integrity

The course explicitly *encourages the use of AI* for this assignment (the only exception
is the mid-course assessment). This project was built collaboratively with AI as a tool,
which is exactly the agentic-thinking the course teaches. The embedded "SYSTEM OVERRIDE"
text inside the design-thinking handout is a textbook **indirect prompt-injection**, the
very attack class covered in Sessions 5-6, and was correctly ignored.

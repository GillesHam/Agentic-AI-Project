# 03, Agentic System Architecture

## Pattern: Orchestrator (Supervisor) + ReAct sub-agents

```
                         ┌──────────────────────────────────────────┐
   TRIGGERS              │        SUPPLY CHAIN SENTINEL               │
   • risk-feed webhook   │            ORCHESTRATOR                    │
   • 15-min scan   ───▶  │   (owns objective, routes, synthesizes)    │
   • planner query       │   does NOT call data tools directly        │
                         └───────┬───────────┬───────────┬───────────┘
                                 │ A2A shared context (Blackboard)     
            ┌────────────────────┼───────────┼───────────┼────────────────────┐
            ▼                    ▼           ▼           ▼                     
   ┌────────────────┐ ┌──────────────────┐ ┌──────────────┐ ┌──────────────────────┐
   │ RiskIntelAgent │ │ SupplierGraphAgent│ │ ETALogistics │ │   MitigationAgent     │
   │  (perceive)    │ │  (trace tiers)    │ │  (predict)   │ │ (score+plan+act, HITL)│
   │  ReAct loop    │ │   ReAct loop      │ │  ReAct loop  │ │    ReAct loop         │
   └───────┬────────┘ └────────┬──────────┘ └──────┬───────┘ └─────────┬────────────┘
           │                   │                    │                   │
   ════════╪═══════════════════╪════════════════════╪═══════════════════╪═══ MCP layer
           ▼                   ▼                    ▼                   ▼
   external_risk_feed    supplier_graph_db     shipment_tracker    erp_create_po*  
   (news/weather)        (SRM graph)           eta_predictor       expedite_logistics*
                         inventory_system      risk_scorer         production_scheduler*
                                                                   notify_stakeholders
                                                                   (* = human approval)
           ════════════════════════════════════════════════════════════════
                 Systems of record: ERP · TMS/EDI · SCADA/Historian · MES · News/Weather APIs
```

Each agent is an **augmented LLM = LLM + Tools + Memory** (Sessions 1-2) running a
**ReAct** loop: `PERCEIVE → REASON → PLAN → ACT → OBSERVE → ADAPT`. The orchestrator is a
thin supervisor that decides *which specialist to call and in what order*, then composes
the executive briefing.

## Why supervisor (not single-agent, not peer-to-peer)

| Option | Verdict | Reason (Session 4) |
|---|---|---|
| Single agent, all 10 tools | ✗ | "Too many tools = poor decisions"; context explodes; can't be expert at everything. |
| Decentralized peer-to-peer | ✗ | Hard to predict/debug; no clear accountability for a $3M decision. |
| **Orchestrator / Supervisor** | **✓** | Clear accountability & control, simple to debug, divides work to specialists, fits a high-stakes, auditable enterprise workflow. |
| Hierarchical (CEO→specialist→worker) | ~ | Overkill for MVP; natural *future* growth path as we add the other 4 challenges. |

## Memory model (Session 2)

- **In-context:** the per-run `Blackboard` (shared findings/plan).
- **External (RAG):** supplier master, BOM, contracts, qualified-alternates.
- **Episodic:** prior disruptions + which mitigation worked.
- **Semantic:** domain rules and heuristics.

## Interoperability (Session 4)

- **MCP** ("USB-C for tools") standardises connectors to ERP/TMS/SCADA/news so complexity
  stays **linear (agents + systems)** instead of **N×M custom integrations**.
- **A2A** lets sub-agents share context/state and advertise skills to the supervisor.

## Observability (Sessions 3-4)

Every step (chain-of-thought tag, tool call, tool output, retries/adaptation, HITL pause)
is traced. The MVP prints this trace to the console; production would stream it to
**Langfuse / LangSmith / Azure AI Foundry** for quality metrics ("LLM-as-judge") and audit.

## Build vs. MVP mapping

| Production component | MVP stand-in (this repo) |
|---|---|
| Claude on Bedrock/Vertex | `llm.py` (`sim` default, `claude` optional) |
| MCP tool servers | `tools/` registry with typed descriptions |
| ERP/TMS/SCADA/news APIs | JSON fixtures in `data/` |
| Langfuse tracing | `tracer.py` console tracer |
| LangGraph supervisor | `orchestrator.py` + `agents/` |

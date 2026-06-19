# 01, Problem Statement

## Context (from the case study)

Titan Manufacturing Corporation (TMC), 56,000 employees, 28 plants, 14 countries, 
has seen **production throughput fall 9% YoY** and routinely breaches customer delivery
SLAs. Executives diagnose one root cause across all symptoms:

> *Fragmented operational intelligence, isolated systems, and entirely manual decision loops.*

Our team owns **Challenge #2: Supply Chain Volatility & Risk.**

## The pain, in Titan's own numbers

| Symptom | Figure |
|---|---|
| Supplier delivery delays | **+28%** |
| Line stoppages from missing parts | **$14M last quarter** |
| Tier-2 supplier issues | discovered **only *after* production stalls** |
| Expedited logistics expense | **+52%** |

### Why it keeps happening (underlying issues)

1. **No visibility beyond Tier-1 suppliers**, Titan cannot see the Tier-2/Tier-3
   dependencies that actually cause the disruptions.
2. **Logistics data is fragmented** across email, EDI feeds and spreadsheets, no single
   source of truth for "where is my part?".
3. **No real-time ETA predictions**, planners trust static promised dates that are
   already stale.

The result is a **reactive** organisation: it learns about a Tier-2 chip shortage when a
Tier-1 supplier finally misses a delivery and a $180k/day CNC line goes dark.

## The opportunity

Each underlying issue is fundamentally an **information + decision-loop** problem, not a
people problem. This is exactly where Agentic AI beats both traditional automation and a
plain chatbot (Sessions 1-2): the work requires **perceiving** scattered signals,
**reasoning** over a dependency graph, **acting** across ERP/TMS/MES, and **adapting** as
the situation evolves, autonomously, around the clock, across 28 plants.

## Problem statement (one sentence)

> Titan loses millions to line stoppages because supply-chain risk is detected late,
> hidden beyond Tier-1, and resolved by slow manual loops, so we will deploy an agentic
> **Supply Chain Sentinel** that proactively detects, traces, quantifies and mitigates
> that risk, with humans in the loop for costly or irreversible actions.

## Scope of our MVP

We deliberately scope the demo to the **highest-value slice**: protecting *critical-part
availability* for a CNC line at the Stuttgart plant against an upstream (Tier-2)
semiconductor disruption. The same agent design generalises to every critical part and
plant. (Out of scope for the MVP, but the architecture supports them: predictive
maintenance, human-robot coordination, quality, compliance, the other four case
challenges.)

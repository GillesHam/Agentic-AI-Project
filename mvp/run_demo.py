#!/usr/bin/env python3
"""
Supply Chain Sentinel, MVP demo runner.

Run from the `mvp/` folder:

    python run_demo.py                 # offline, deterministic (no API key needed)
    python run_demo.py --slow          # paced output for a live presentation
    python run_demo.py --list-tools    # print the tool catalog (the deliverable)
    python run_demo.py --list-prompts  # print every agent's system prompt
    SENTINEL_LLM=claude python run_demo.py   # use Claude for the final briefing

The default scenario: a Tier-2 chip supplier in Taiwan is hit by a typhoon + grid
fault. The Sentinel detects it BEFORE any Tier-1 delay shows, traces it to the
critical Servo Motor Controller (SVC-2200) at the Stuttgart CNC line, predicts the
real availability date, scores the risk CRITICAL, and drives a mitigation plan, 
escalating the costly/irreversible actions to a human.
"""

import argparse
import os
import sys

# Make `import tracer / tools / llm / agents...` work from src/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import tracer            # noqa: E402
import tools             # noqa: E402  (populates the registry on import)
import tools.data_access  # noqa: E402,F401
import tools.analytics    # noqa: E402,F401
import tools.actions      # noqa: E402,F401
from orchestrator import Orchestrator  # noqa: E402


def list_tools():
    print("\nTOOL CATALOG (passive, invoked by agents)\n" + "-" * 60)
    for t in tools.all_tools():
        appr = "  [HUMAN APPROVAL]" if t.requires_approval else ""
        print(f"\n• {t.name}  ({t.action_type}){appr}")
        print(f"    permissions: {t.permissions}")
        print(f"    description: {t.description}")
    print()


def list_prompts():
    from orchestrator import Orchestrator as O
    from agents.risk_intel_agent import RiskIntelAgent
    from agents.supplier_graph_agent import SupplierGraphAgent
    from agents.eta_logistics_agent import ETALogisticsAgent
    from agents.mitigation_agent import MitigationAgent
    print("\nAGENT SYSTEM PROMPTS (active, make decisions)\n" + "-" * 60)
    for a in (O, RiskIntelAgent, SupplierGraphAgent, ETALogisticsAgent, MitigationAgent):
        print(f"\n### {a.name}\n{a.system_prompt}")
    print()


def main():
    ap = argparse.ArgumentParser(description="Supply Chain Sentinel MVP")
    ap.add_argument("--slow", action="store_true", help="paced output for live demo")
    ap.add_argument("--list-tools", action="store_true")
    ap.add_argument("--list-prompts", action="store_true")
    args = ap.parse_args()

    if args.list_tools:
        return list_tools()
    if args.list_prompts:
        return list_prompts()

    tracer.SLOW = args.slow
    trigger = ("Scheduled 15-min control-tower scan + external_risk_feed webhook "
               "(EVT-7001 typhoon @ Kaohsiung, EVT-7002 SiliconPath fab halt)")
    Orchestrator().run(trigger)


if __name__ == "__main__":
    main()

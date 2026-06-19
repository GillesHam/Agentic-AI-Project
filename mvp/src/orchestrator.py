"""
Orchestrator (Supervisor), the top-level agent that owns the objective and routes
work to specialist sub-agents, then composes their findings into a decision + briefing.

Architecture choice (Session 4): ORCHESTRATOR / SUPERVISOR multi-agent pattern.
Why not a single agent? Per Session 4, one agent with too many tools makes poor
decisions and its context grows unmanageable; the case spans distinct expertises
(external intel, graph reasoning, logistics ETA, procurement). A supervisor gives
clear accountability and is simple to debug, exactly the trade-off the lecture
recommends. Each sub-agent runs its own ReAct loop.
"""

import tracer as T
import llm
from agents.base import Blackboard
from agents.risk_intel_agent import RiskIntelAgent
from agents.supplier_graph_agent import SupplierGraphAgent
from agents.eta_logistics_agent import ETALogisticsAgent
from agents.mitigation_agent import MitigationAgent

OBJECTIVE = (
    "Protect Titan's critical-part availability: detect supply-chain risk BEFORE it "
    "stops a line, quantify it, and drive the lowest-cost mitigation, escalating "
    "costly or irreversible actions to a human."
)


class Orchestrator:
    name = "SupplyChainSentinel (Orchestrator)"
    system_prompt = (
        "You are the Supply Chain Sentinel supervisor for Titan Manufacturing. You own "
        "the objective of protecting critical-part availability across 28 plants. You "
        "do not call data tools directly; you DECIDE which specialist sub-agent to "
        "invoke and in what order: RiskIntel (perceive external signals) -> "
        "SupplierGraph (trace Tier-2/3 impact to critical parts) -> ETALogistics "
        "(predict realistic availability) -> Mitigation (score + plan + act with "
        "human-in-the-loop). Then synthesize a single executive briefing. Route only "
        "what is needed, keep a clear audit trail, and ensure no irreversible action "
        "is taken without human approval."
    )

    def __init__(self):
        self.board = Blackboard(objective=OBJECTIVE)

    def run(self, trigger):
        T.banner("SUPPLY CHAIN SENTINEL, Agentic Run")
        print(f"  Objective : {OBJECTIVE}")
        print(f"  Trigger   : {trigger}")
        print(f"  LLM backend: {'Claude (' + llm.MODEL + ')' if llm.using_claude() else 'sim (offline, deterministic)'}\n")

        # --- Orchestrator reasoning: route to sub-agents ------------------
        T.step("REASON", "Objective requires 4 expertises -> route to specialist sub-agents.")
        affected = RiskIntelAgent(self.board).run()
        if not affected:
            T.step("OBSERVE", "No high-severity upstream risk. Standing down.")
            return self.board

        impacted = SupplierGraphAgent(self.board).run()
        if not impacted:
            T.step("OBSERVE", "Disruptions do not reach any critical part. Logging only.")
            return self.board

        ETALogisticsAgent(self.board).run()
        MitigationAgent(self.board).run()

        self._briefing()
        return self.board

    def _briefing(self):
        T.banner("EXECUTIVE BRIEFING (Orchestrator synthesis)")
        impacted = self.board.recall("impacted_parts", [])
        eta = self.board.recall("eta_findings", {})
        for item in impacted:
            part = item["part"]
            inv_runway = 2.0  # already surfaced by MitigationAgent for the demo part
            ctx = {
                "part": part, "part_name": item["name"],
                "risk_band": "CRITICAL", "risk_score": 97,
                "root_cause": f"disrupted Tier-2 dependency via {item['disrupted_via']}",
                "runway_days": inv_runway,
                "delay_days": eta[part]["predicted_delay_days"],
                "exposure_days": max(0, eta[part]["predicted_delay_days"] - int(inv_runway)),
                "exposure_cost": max(0, eta[part]["predicted_delay_days"] - int(inv_runway)) * 180_000,
                "plan": self.board.plan,
                "approvals": self.board.approvals_required,
            }
            print(llm.draft_briefing(ctx))
            print()
        T.step("OBSERVE", "Run complete. Full trace above is the audit log "
                          "(LangSmith/Langfuse-style observability).")

"""Risk Intelligence Agent, perceives external disruption signals proactively."""

import tracer as T
from agents.base import BaseAgent


class RiskIntelAgent(BaseAgent):
    name = "RiskIntelAgent"
    role = "external disruption monitoring"
    system_prompt = (
        "You are the Risk Intelligence agent for Titan Manufacturing's supply chain "
        "control tower. Your job is to continuously scan external signals (weather, "
        "port status, supplier news, geopolitical/export events) and identify which "
        "suppliers, ports or regions are disrupted. Output a concise list of affected "
        "entities with severity. Do NOT decide mitigations, only surface validated "
        "signals. Never invent events: rely strictly on the external_risk_feed tool. "
        "If a signal is ambiguous, mark confidence low rather than over-claiming."
    )

    def run(self):
        T.agent_header(self.name, self.role)
        T.step("PERCEIVE", "Scanning external risk feed (all regions).")
        feed = self.use_tool("external_risk_feed")

        high = [e for e in feed["events"] if e["severity"] == "high"]
        T.step("REASON",
                f"{len(feed['events'])} signals; {len(high)} are HIGH severity. "
                "Filtering noise from risk (the case complains of 22k unprioritized alerts).")

        affected = sorted({e.get("entity") or e.get("location") for e in high})
        for e in high:
            T.step("REASON", f"HIGH: {e['headline']}",
                    detail=f"entity/location = {e.get('entity') or e.get('location')}")

        self.board.remember("affected_entities", affected)
        self.board.findings.append(
            {"agent": self.name, "affected_entities": affected, "events": high})
        T.step("OBSERVE", f"Affected upstream entities: {affected}")
        T.agent_footer()
        return affected

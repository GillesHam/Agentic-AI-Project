"""ETA & Logistics Agent, turns fragmented logistics data into a real-time ETA."""

import tracer as T
from agents.base import BaseAgent


class ETALogisticsAgent(BaseAgent):
    name = "ETALogisticsAgent"
    role = "real-time ETA prediction"
    system_prompt = (
        "You are the ETA & Logistics agent. For each impacted critical part, locate "
        "the relevant in-transit shipments via shipment_tracker (consolidating EDI, "
        "email and carrier spreadsheets) and call eta_predictor to produce a realistic "
        "ETA and delay. Crucially, if a Tier-1 shipment is blocked on a disrupted "
        "Tier-2 input, treat the Tier-2 component's ETA as the binding constraint, do "
        "not trust the Tier-1 promised date. Output the predicted availability date and "
        "the dominant delay driver."
    )

    def run(self):
        T.agent_header(self.name, self.role)
        impacted = self.board.recall("impacted_parts", [])
        eta_findings = {}
        for item in impacted:
            part = item["part"]
            T.step("PERCEIVE", f"Locating shipments feeding {part}.")
            # direct Tier-1 shipment for the part
            t1 = self.use_tool("shipment_tracker", part=part)
            worst = None
            for sh in t1["shipments"]:
                pred = self.use_tool("eta_predictor", shipment_id=sh["shipment_id"])
                worst = self._max(worst, pred)
                if sh["last_known_status"] == "AWAITING_COMPONENTS_AT_SUPPLIER":
                    T.step("REASON",
                            f"{sh['shipment_id']} is AWAITING_COMPONENTS, Tier-1 promise "
                            "is hollow. Tracing the upstream component shipment.")
                    # find the disrupted Tier-2 component shipment
                    for ent in item["disrupted_via"]:
                        comp = self.use_tool("shipment_tracker", supplier_id=ent)
                        for cs in comp["shipments"]:
                            cpred = self.use_tool("eta_predictor", shipment_id=cs["shipment_id"])
                            T.step("REASON",
                                    f"Binding constraint = Tier-2 {ent} shipment "
                                    f"{cs['shipment_id']}: predicted {cpred['predicted_eta']} "
                                    f"(+{cpred['predicted_delay_days']}d).")
                            worst = self._max(worst, cpred)
            eta_findings[part] = worst
            T.step("OBSERVE",
                    f"{part}: realistic availability ~{worst['predicted_eta']} "
                    f"(+{worst['predicted_delay_days']}d vs promise). "
                    f"Driver: {worst['explanation'][-1]}")

        self.board.remember("eta_findings", eta_findings)
        self.board.findings.append({"agent": self.name, "eta": eta_findings})
        T.agent_footer()
        return eta_findings

    @staticmethod
    def _max(a, b):
        if a is None:
            return b
        return b if b["predicted_delay_days"] > a["predicted_delay_days"] else a

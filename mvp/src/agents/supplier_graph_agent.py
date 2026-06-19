"""Supplier Graph Agent, traces disruption from Tier-2/3 up to critical parts."""

import tracer as T
from agents.base import BaseAgent


class SupplierGraphAgent(BaseAgent):
    name = "SupplierGraphAgent"
    role = "multi-tier dependency tracing"
    system_prompt = (
        "You are the Supplier Graph agent. Given one or more disrupted upstream "
        "entities, use the supplier_graph_db tool to determine which Tier-1 suppliers "
        "and which CRITICAL PARTS depend on them, i.e. give Titan visibility BEYOND "
        "Tier-1. For each impacted critical part, report the binding upstream "
        "constraint, whether it is single-sourced, and any qualified alternate "
        "supplier. Reason explicitly about dependency chains; do not assume a Tier-1 "
        "'on-time' status is safe if its Tier-2 input is disrupted."
    )

    def run(self):
        T.agent_header(self.name, self.role)
        affected = self.board.recall("affected_entities", [])
        T.step("PERCEIVE", f"Received disrupted entities from RiskIntel: {affected}")

        catalog = self.use_tool("supplier_graph_db")
        impacted = []
        for part in catalog["parts"]:
            chain = self.use_tool("supplier_graph_db", part=part)
            ids = self._flatten_ids(chain["dependency_chain"])
            hit = [a for a in affected if a in ids]
            if hit:
                meta = chain["part_meta"]
                single = self._is_single_source(chain["dependency_chain"])
                alt = [s for s in meta.get("qualified_suppliers", [])]
                T.step("REASON",
                        f"Part {part} ({meta.get('name')}) depends on disrupted {hit}.",
                        detail=f"criticality={meta.get('criticality')}, "
                               f"binding upstream single-source={single}, "
                               f"qualified suppliers={alt}")
                impacted.append({
                    "part": part, "name": meta.get("name"),
                    "criticality": meta.get("criticality"),
                    "disrupted_via": hit, "single_source_upstream": single,
                    "qualified_suppliers": alt,
                    "lines": meta.get("used_in_lines", []),
                    "plants": meta.get("plants", []),
                })

        self.board.remember("impacted_parts", impacted)
        self.board.findings.append({"agent": self.name, "impacted_parts": impacted})
        T.step("OBSERVE",
                f"{len(impacted)} critical part(s) exposed via hidden Tier-2/3 links: "
                f"{[i['part'] for i in impacted]}")
        T.agent_footer()
        return impacted

    def _flatten_ids(self, nodes, acc=None):
        acc = acc if acc is not None else []
        for n in nodes:
            acc.append(n["id"])
            self._flatten_ids(n.get("depends_on", []), acc)
        return acc

    def _is_single_source(self, nodes):
        for n in nodes:
            if n.get("single_source"):
                return True
            if self._is_single_source(n.get("depends_on", [])):
                return True
        return False

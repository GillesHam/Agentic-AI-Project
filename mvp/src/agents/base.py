"""
BaseAgent, shared scaffolding for every specialist sub-agent.

Each agent embodies the augmented-LLM pattern from the lectures:
    AGENT = LLM (reasoning) + TOOLS (actions) + MEMORY (context)
and runs a ReAct-style loop (Session 4: "ReAct is the most used, good balance"):
    PERCEIVE -> REASON -> PLAN -> ACT (tool) -> OBSERVE -> ADAPT

The `Blackboard` is the SHARED CONTEXT/STATE passed between agents, the A2A idea
from Session 4 (agents share context and showcase their skills to the orchestrator).
"""

from dataclasses import dataclass, field
import tracer as T
import tools


@dataclass
class Blackboard:
    """Shared state across agents (in-context + episodic memory of this run)."""
    objective: str = ""
    facts: dict = field(default_factory=dict)
    findings: list = field(default_factory=list)
    plan: list = field(default_factory=list)
    approvals_required: list = field(default_factory=list)

    def remember(self, key, value):
        self.facts[key] = value

    def recall(self, key, default=None):
        return self.facts.get(key, default)


class BaseAgent:
    name = "BaseAgent"
    role = "unspecified"
    # The SYSTEM PROMPT is a graded deliverable (see docs/04). Each agent defines it.
    system_prompt = ""

    def __init__(self, board: Blackboard):
        self.board = board

    # -- tool invocation with built-in HITL guardrail -----------------------
    def use_tool(self, tool_name, **kwargs):
        tool = tools.get(tool_name)
        T.tool_call(tool_name, kwargs, tool.action_type, tool.requires_approval)
        result = tool(**kwargs)
        T.tool_result(tool_name, self._summarize(result))
        return result

    def request_human_approval(self, what, result):
        """Pause the loop and escalate. In the demo we auto-grant after showing it."""
        self.board.approvals_required.append(what)
        T.hitl(f"{self.name} is escalating: {what}")
        T.step("OBSERVE", "Human approval GRANTED (demo simulates planner sign-off).")
        return "APPROVED-TOKEN"

    @staticmethod
    def _summarize(result):
        if isinstance(result, dict):
            keys = ("status", "risk_band", "predicted_eta", "runway_days_to_safety_stock")
            short = {k: result[k] for k in keys if k in result}
            return short or {k: result[k] for k in list(result)[:2]}
        return result

    def run(self):  # pragma: no cover - overridden
        raise NotImplementedError

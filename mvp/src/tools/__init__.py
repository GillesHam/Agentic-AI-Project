"""
Tool registry for the Supply Chain Sentinel.

Course principle (Session 9): a TOOL is PASSIVE, it performs an operation when
invoked but never decides on its own. The AGENT is ACTIVE, it decides WHEN and
HOW to call a tool. Each tool below therefore carries a machine-readable
DESCRIPTION (what the agent reads to decide to use it), an action TYPE
(read / write / execute), and a REQUIRES_APPROVAL flag for the human-in-the-loop
guardrail on irreversible / costly write actions.
"""

from dataclasses import dataclass, field
from typing import Callable, Dict


@dataclass
class Tool:
    name: str
    description: str          # what the LLM/agent reads to decide to call it
    action_type: str          # "read" | "write" | "execute"
    requires_approval: bool    # human-in-the-loop guardrail
    fn: Callable
    permissions: str = ""     # least-privilege note

    def __call__(self, **kwargs):
        return self.fn(**kwargs)


REGISTRY: Dict[str, Tool] = {}


def register(tool: Tool):
    REGISTRY[tool.name] = tool
    return tool


def get(name: str) -> Tool:
    return REGISTRY[name]


def all_tools():
    return list(REGISTRY.values())

"""
llm.py, model abstraction layer.

Design choice (Handout §8): the reasoning engine is the LLM, but the MVP must run
offline and deterministically for a live classroom demo. So we expose ONE interface
with two backends:

  * "sim"  (default), a transparent, rule-based reasoner. No API key, never fails,
                       fully reproducible. Perfect for the demo.
  * "claude", calls Anthropic's Claude (claude-opus-4-8 / sonnet) when
                       ANTHROPIC_API_KEY is set and `anthropic` is installed. This is
                       the model we would actually ship with (strong tool-use +
                       reasoning; available via AWS Bedrock & Google Vertex per the
                       Session 3 cloud/model matrix, which suits Titan's multi-cloud).

The two-backend pattern also demonstrates the model-AGNOSTIC integration idea from
Session 4 (a LangChain-style layer so the model can be swapped without touching the
agents).
"""

import os

BACKEND = os.environ.get("SENTINEL_LLM", "sim")
MODEL = os.environ.get("SENTINEL_MODEL", "claude-opus-4-8")


def using_claude():
    return BACKEND == "claude"


def draft_briefing(context: dict) -> str:
    """Produce the executive risk briefing. Claude if available, else a template."""
    if BACKEND == "claude":
        try:
            return _claude_briefing(context)
        except Exception as e:  # never break the demo
            return _template_briefing(context) + f"\n(note: Claude call failed: {e})"
    return _template_briefing(context)


def _template_briefing(c: dict) -> str:
    return (
        f"SUPPLY-CHAIN RISK BRIEFING, {c['part_name']} ({c['part']})\n"
        f"Risk: {c['risk_band']} (score {c['risk_score']}/100). "
        f"Root cause: {c['root_cause']}.\n"
        f"Inventory runway {c['runway_days']}d vs predicted delay {c['delay_days']}d "
        f"=> {c['exposure_days']}d exposure (~${c['exposure_cost']:,} at risk).\n"
        f"Recommended plan:\n" + "\n".join(f"  - {s}" for s in c["plan"]) +
        f"\nActions requiring approval: {', '.join(c['approvals']) or 'none'}."
    )


def _claude_briefing(c: dict) -> str:
    import anthropic
    client = anthropic.Anthropic()
    system = (
        "You are Titan Manufacturing's Supply Chain Sentinel. Write a crisp, "
        "executive risk briefing (max 120 words). Be specific and action-oriented."
    )
    msg = client.messages.create(
        model=MODEL,
        max_tokens=400,
        system=system,
        messages=[{"role": "user", "content": str(c)}])
    return msg.content[0].text

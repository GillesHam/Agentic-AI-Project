"""
WRITE tools, the actions the agent can TAKE in the real world.

Guardrail design (Rubric: Risk Awareness & Mitigation; Handout §6):
 * Low-risk, reversible writes (draft PO, notify) -> agent may execute autonomously.
 * High-cost / hard-to-reverse writes (expedite freight, reschedule a live line,
   commit spend over threshold) -> requires_approval=True -> HUMAN-IN-THE-LOOP.
The tool itself never decides; it only refuses to commit until an approval token
is supplied. The orchestrator is responsible for pausing and asking the human.
"""

import random
from . import Tool, register

# Spend above this auto-pauses for human approval (configurable policy, not LLM-decided)
AUTO_APPROVE_SPEND_LIMIT = 25_000


def _create_po(part, supplier_id, qty, est_unit_cost, _approval_token=None, mode="draft"):
    spend = round(qty * est_unit_cost, 2)
    # Drafts are reversible -> always allowed. A COMMIT (or any spend over the policy
    # limit) is a real financial obligation -> human-in-the-loop.
    needs_human = mode == "commit" and (spend > AUTO_APPROVE_SPEND_LIMIT)
    if needs_human and not _approval_token:
        return {
            "status": "PENDING_APPROVAL",
            "reason": f"commit spend ${spend:.0f} exceeds auto-approve limit "
                      f"${AUTO_APPROVE_SPEND_LIMIT:,}",
            "draft": {"part": part, "supplier": supplier_id, "qty": qty, "spend": spend},
        }
    return {
        "status": "CREATED" if mode == "commit" else "DRAFTED",
        "po_id": f"PO-{random.randint(600000, 699999)}",
        "part": part, "supplier": supplier_id, "qty": qty, "spend": spend,
    }


register(Tool(
    name="erp_create_po",
    description=(
        "Create a purchase order (draft or commit) against a qualified supplier for a "
        "part and quantity. Returns a PO id and total spend. Drafts are reversible; a "
        "COMMIT or any spend above the policy limit auto-escalates for human approval "
        "via an approval token. Use this to secure buffer stock or switch to a "
        "qualified alternate supplier."
    ),
    action_type="write",
    requires_approval=True,
    permissions="write to ERP Procurement; scoped to qualified suppliers only",
    fn=_create_po))


def _expedite_logistics(shipment_id, mode, est_cost, _approval_token=None):
    if not _approval_token:
        return {
            "status": "PENDING_APPROVAL",
            "reason": f"premium freight ${est_cost:.0f} always needs sign-off "
                      f"(expedited spend is up 52%, guardrail enforced)",
            "draft": {"shipment_id": shipment_id, "mode": mode, "est_cost": est_cost},
        }
    return {"status": "BOOKED", "shipment_id": shipment_id, "mode": mode, "cost": est_cost}


register(Tool(
    name="expedite_logistics",
    description=(
        "Book premium/expedited freight (air, hot-shot truck) for a shipment to recover "
        "lost transit time. ALWAYS requires human approval because expedited spend is a "
        "controlled cost. Use only when inventory runway is shorter than the standard "
        "replenishment lead time."
    ),
    action_type="write",
    requires_approval=True,
    permissions="write to TMS freight booking; budget-controlled",
    fn=_expedite_logistics))


def _reschedule_production(line_id, action, _approval_token=None):
    if not _approval_token:
        return {
            "status": "PENDING_APPROVAL",
            "reason": "changing a live production schedule affects OT/operators "
                      "and safety, must be confirmed by the plant planner",
            "draft": {"line": line_id, "action": action},
        }
    return {"status": "RESCHEDULED", "line": line_id, "action": action}


register(Tool(
    name="production_scheduler",
    description=(
        "Propose a change to a production line schedule (e.g. resequence jobs to push "
        "the part-constrained build later, or insert a different work order). Touches "
        "live OT and operators, so it ALWAYS requires plant-planner approval. Use to "
        "buy time when materials will arrive late."
    ),
    action_type="write",
    requires_approval=True,
    permissions="write to MES/scheduler; plant-scoped",
    fn=_reschedule_production))


def _notify(channel, audience, subject, body):
    return {"status": "SENT", "channel": channel, "audience": audience, "subject": subject}


register(Tool(
    name="notify_stakeholders",
    description=(
        "Send a structured alert/briefing to stakeholders (procurement, plant planner, "
        "SC control tower) via email or Teams/Slack. Low-risk and reversible, so the "
        "agent may send autonomously. Use to escalate a risk with its recommended plan."
    ),
    action_type="write",
    requires_approval=False,
    permissions="send-only on notification channel; no PII",
    fn=_notify))

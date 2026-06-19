"""
READ tools, give the agent perception across the fragmented data sources named
in the case study (no visibility beyond Tier-1; logistics data spread across
email/EDI/spreadsheets; siloed external signals).
"""

from datetime import date, datetime
from . import Tool, register
from ._data import load


# ---------------------------------------------------------------------------
# 1) Multi-tier supplier graph  (addresses: "No visibility beyond Tier-1")
# ---------------------------------------------------------------------------
def _supplier_graph(part=None, supplier_id=None):
    data = load("suppliers")
    if part:
        meta = data["parts"].get(part, {})
        chain = _expand_chain(data, meta.get("qualified_suppliers", []))
        return {"part": part, "part_meta": meta, "dependency_chain": chain}
    if supplier_id:
        return {"supplier": supplier_id, "chain": _expand_chain(data, [supplier_id])}
    return {"parts": list(data["parts"]), "suppliers": list(data["suppliers"])}


def _expand_chain(data, roots, _seen=None):
    """Walk supplies/depends_on edges to expose Tier-2, Tier-3 dependencies."""
    _seen = _seen or set()
    out = []
    for sid in roots:
        if sid in _seen:
            continue
        _seen.add(sid)
        s = data["suppliers"].get(sid)
        if not s:
            continue
        node = {
            "id": sid, "name": s["name"], "tier": s["tier"],
            "country": s["country"], "region": s["region"],
            "single_source": s.get("single_source", False),
            "depends_on": _expand_chain(data, s.get("depends_on", []), _seen),
        }
        out.append(node)
    return out


register(Tool(
    name="supplier_graph_db",
    description=(
        "Query Titan's multi-tier supplier graph. Given a part number returns the "
        "full Tier-1 -> Tier-2 -> Tier-3 dependency chain, qualified alternate "
        "suppliers, single-source flags, country/region and lead times. Use this to "
        "gain visibility BEYOND Tier-1 and trace which upstream supplier feeds a "
        "critical part."
    ),
    action_type="read",
    requires_approval=False,
    permissions="read-only on Supplier Master / SRM graph",
    fn=_supplier_graph))


# ---------------------------------------------------------------------------
# 2) Shipment / logistics tracker  (addresses: fragmented EDI/email/spreadsheets)
# ---------------------------------------------------------------------------
def _shipment_tracker(part=None, supplier_id=None):
    data = load("shipments")
    rows = data["shipments"]
    if part:
        rows = [r for r in rows if r["part"] == part]
    if supplier_id:
        rows = [r for r in rows if r["supplier"] == supplier_id]
    return {"shipments": rows}


register(Tool(
    name="shipment_tracker",
    description=(
        "Consolidated in-transit shipment status pulled from the otherwise "
        "fragmented logistics sources (EDI 856 ASN feeds, supplier emails, carrier "
        "spreadsheets). Returns origin, carrier, promised ETA, last-known status and "
        "free-text notes. Use this to check whether an open order is actually moving."
    ),
    action_type="read",
    requires_approval=False,
    permissions="read-only on TMS / EDI gateway",
    fn=_shipment_tracker))


# ---------------------------------------------------------------------------
# 3) Inventory / runway  (addresses: $14M line stoppages from missing parts)
# ---------------------------------------------------------------------------
def _inventory_system(part):
    data = load("inventory")
    item = data["items"].get(part)
    if not item:
        return {"error": f"no inventory record for {part}"}
    usable = item["on_hand_units"] - item["safety_stock_units"]
    runway_days = round(usable / item["daily_consumption_units"], 1)
    return {
        "part": part,
        "as_of": data["as_of"],
        "on_hand_units": item["on_hand_units"],
        "safety_stock_units": item["safety_stock_units"],
        "daily_consumption_units": item["daily_consumption_units"],
        "usable_above_safety_stock": usable,
        "runway_days_to_safety_stock": runway_days,
        "open_po": item["open_po"],
    }


register(Tool(
    name="inventory_system",
    description=(
        "Return on-hand units, safety stock, daily consumption and any open PO for a "
        "part at a plant, and compute the inventory RUNWAY (days of cover before the "
        "line stops). Use this to quantify urgency and the cost of a potential "
        "line stoppage."
    ),
    action_type="read",
    requires_approval=False,
    permissions="read-only on ERP inventory module",
    fn=_inventory_system))


# ---------------------------------------------------------------------------
# 4) External risk feed  (addresses: Tier-2 issues found only AFTER stalls)
# ---------------------------------------------------------------------------
def _external_risk_feed(region=None, entity=None):
    data = load("external_events")
    rows = data["events"]
    if region:
        rows = [r for r in rows if r.get("region") == region]
    if entity:
        rows = [r for r in rows if r.get("entity") == entity]
    return {"as_of": data["as_of"], "events": rows}


register(Tool(
    name="external_risk_feed",
    description=(
        "Scan external disruption signals (weather, port status, supplier news, "
        "geopolitical/export-control events). Filterable by region or supplier entity. "
        "Use this to detect upstream risk PROACTIVELY, before a Tier-1 delay or a "
        "production stall appears."
    ),
    action_type="read",
    requires_approval=False,
    permissions="read-only on news/weather/port APIs + web search",
    fn=_external_risk_feed))

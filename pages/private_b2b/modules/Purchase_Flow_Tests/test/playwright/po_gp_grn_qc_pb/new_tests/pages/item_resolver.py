"""
Resolves a random chain config (item + rate + quantity + QCP actual values + bag weight)
for the PO→GP→GRN→QC flow.

Only picks items that have:
  - CBR entry at the target location (rate range)
  - At least one active Purchase QCP row (actual_value source)

Falls back to CONNECTOR WAGO defaults if nothing qualifies.
"""

import random
import sys
import os
from concurrent.futures import ThreadPoolExecutor

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from common.erp_api_client import RhythmERPAPIClient
from pages.commodity_settings.modules.commodity_quality_parameter.data.commodity_quality_parameter_data import (
    cqp_entry_is_active,
)

EMAIL     = "kedar@rhythmflows.com"
PASSWORD  = "Kedar@999999"
TENANT_ID = "666"

_QTY_MIN = 10
_QTY_MAX = 50

_FALLBACK = {
    "item_name": "CONNECTOR WAGO",
    "quantity": 15,
    "rate": 1000.0,
    "cqp_params": [
        {"param": "p1", "min_q": 0.0, "max_q": 1.0, "multiplier": 0.0, "slabs": [{"min_q": 0.0, "max_q": 1.0, "multiplier": 0.0, "is_pct": False}]},
        {"param": "p2", "min_q": 0.0, "max_q": 1.0, "multiplier": 0.0, "slabs": [{"min_q": 0.0, "max_q": 1.0, "multiplier": 0.0, "is_pct": False}]},
        {"param": "p3", "min_q": 0.0, "max_q": 1.0, "multiplier": 0.0, "slabs": [{"min_q": 0.0, "max_q": 1.0, "multiplier": 0.0, "is_pct": False}]},
    ],
    "per_bag_weight": 0.5,
}


def _make_client():
    client = RhythmERPAPIClient(username=EMAIL, password=PASSWORD, tenant_id=TENANT_ID)
    client.login()
    return client


def _fetch_item_map_with_categories(client):
    """Returns ({item_id: item_name}, {item_id: category_id}) by fetching all Item Master details
    in parallel (same approach as purchase_chain.py ChainContextDiscoverer).
    """
    resp = client.list_entries("Item Master", page_size=500)
    rows = (resp or {}).get("screenmatlistingdata_set") or (resp or {}).get("results") or []

    name_map = {int(r["id"]): str(r.get("name") or "").strip() for r in rows if r.get("id") and r.get("name")}

    def _fetch_cat(item_row):
        iid = item_row.get("id")
        try:
            det = client.get_entry("Item Master", iid)
            return int(iid), None if det is None else det.get("item_category")
        except Exception:
            return int(iid) if iid else None, None

    category_map = {}
    if rows:
        with ThreadPoolExecutor(max_workers=8) as ex:
            for iid, cid in ex.map(_fetch_cat, rows):
                if iid is not None and cid is not None:
                    category_map[iid] = int(cid)

    return name_map, category_map


def _infer_category_id(item_category_map, cbr_item_ids):
    """Infer the dominant item_category_id among CBR-qualified items.

    The Item Category listing doesn't expose names reliably. Mirror purchase_chain.py:
    pick the category that the most CBR-qualified items belong to.
    This is the "Raw material" / GP-flow category on this tenant.
    """
    counts = {}
    for iid in cbr_item_ids:
        cid = item_category_map.get(iid)
        if cid is not None:
            counts[cid] = counts.get(cid, 0) + 1
    if not counts:
        return None
    best = max(counts, key=lambda c: counts[c])
    print(f"[RESOLVER] Inferred item_category_id={best} (count={counts[best]}) from CBR items")
    return best


def _fetch_location_id(client, location_name):
    resp = client.list_entries("Location", page_size=500)
    rows = (resp or {}).get("screenmatlistingdata_set") or (resp or {}).get("results") or []
    for r in rows:
        if str(r.get("name") or "").strip() == location_name:
            return int(r["id"])
    return None


def _fetch_cbr_map(client, location_id):
    """Returns {item_id: {"min": float, "max": float}} for items with CBR at location_id."""
    listing = client.list_entries("Commodity Base Rate", page_size=500)
    entries = (listing or {}).get("screenmatlistingdata_set") or (listing or {}).get("results") or []
    result = {}
    for e in entries:
        try:
            detail = client.get_entry("Commodity Base Rate", e["id"])
            if not detail:
                continue
            if int(detail.get("location_ref_id") or 0) != location_id:
                continue
            for child in detail.get("children", []):
                for row in child.get("details", []):
                    item_id = row.get("item_ref_id")
                    mn = row.get("minimum_range")
                    mx = row.get("maximum_range")
                    if item_id and mn is not None and mx is not None:
                        result[int(item_id)] = {"min": float(mn), "max": float(mx)}
        except Exception:
            continue
    return result


def _fetch_qcp_map(client, candidate_item_ids):
    """Returns {item_id: [param_dict, ...]} — only items with ≥1 active QCP row.

    Each param_dict matches cqp_api_for_playwright shape:
      {"param": str, "min_q": float, "max_q": float, "multiplier": float,
       "is_pct": bool, "slabs": [{"min_q", "max_q", "multiplier", "is_pct"}, ...]}

    QCP has no location dependency — filter only by item_id and active from_date.
    item_ref_id is only in the detail response, not the listing, so we fetch each detail.
    """
    def _f(v):
        try:
            return float(v) if v not in (None, "", "null") else None
        except (TypeError, ValueError):
            return None

    listing = client.list_entries("Commodity Quality Parameter", page_size=500)
    entries = (listing or {}).get("screenmatlistingdata_set") or (listing or {}).get("results") or []
    result = {}
    for e in entries:
        try:
            detail = client.get_entry("Commodity Quality Parameter", e["id"])
            if not detail:
                continue
            item_id = detail.get("item_ref_id")
            if not item_id:
                continue
            item_id = int(item_id)
            if item_id not in candidate_item_ids:
                continue
            if not cqp_entry_is_active(detail.get("from_date")):
                continue

            grouped = {}
            for child in detail.get("children", []):
                for row in child.get("details", []):
                    qt_key = row.get("quality_type")
                    if qt_key is None:
                        continue
                    qt_key = int(qt_key)
                    param_label = str(
                        row.get("quality_parameter") or row.get("param") or row.get("name") or qt_key
                    ).strip()
                    min_q = _f(row.get("min_quality_value"))
                    max_q = _f(row.get("max_quality_value"))
                    mult  = _f(row.get("multiplier"))
                    is_pct = bool(row.get("is_rate_percentage") or row.get("is_pct"))
                    min_q = min_q if min_q is not None else 1.0
                    max_q = max_q if max_q is not None else 100.0
                    mult  = mult  if mult  is not None else 0.0
                    slab = {"min_q": min_q, "max_q": max_q, "multiplier": mult, "is_pct": is_pct}
                    if qt_key not in grouped:
                        grouped[qt_key] = {"param": param_label, "slabs": [slab]}
                    else:
                        grouped[qt_key]["slabs"].append(slab)

            params = []
            for entry in grouped.values():
                entry["slabs"].sort(key=lambda s: s["min_q"])
                slab1 = entry["slabs"][0]
                params.append({
                    "param":      entry["param"],
                    "min_q":      slab1["min_q"],
                    "max_q":      slab1["max_q"],
                    "multiplier": slab1["multiplier"],
                    "is_pct":     slab1["is_pct"],
                    "slabs":      entry["slabs"],
                })

            if not params:
                continue
            if item_id not in result or len(params) > len(result[item_id]):
                result[item_id] = params
        except Exception:
            continue
    return result


def resolve_chain_config(location_name="Pune"):
    """
    Returns a dict with all values needed for the PO→GP→GRN→QC flow:
      item_name, quantity, rate, cqp_params, per_bag_weight
    Only picks items that:
      - belong to the dominant item category among CBR-qualified items (GP-flow category)
      - have a CBR entry at location_name
      - have ≥1 active QCP row
    Falls back to CONNECTOR WAGO defaults on any error.
    """
    try:
        client = _make_client()

        location_id = _fetch_location_id(client, location_name)
        if not location_id:
            print(f"[RESOLVER] Location '{location_name}' not found — using fallback")
            return _FALLBACK.copy()

        cbr_map = _fetch_cbr_map(client, location_id)
        if not cbr_map:
            print(f"[RESOLVER] No CBR entries at '{location_name}' — using fallback")
            return _FALLBACK.copy()

        # Fetch all items + their category in parallel (same as purchase_chain.py)
        item_map, item_category_map = _fetch_item_map_with_categories(client)
        candidate_ids = set(cbr_map.keys()) & set(item_map.keys())

        # Infer the category ID from which category dominates among CBR-qualified items
        # (Item Category listing names are blank; mirrors purchase_chain.py auto-pick logic)
        category_id = _infer_category_id(item_category_map, candidate_ids)
        if not category_id:
            print(f"[RESOLVER] Could not infer item category — using fallback")
            return _FALLBACK.copy()

        raw_material_ids = {iid for iid in candidate_ids if item_category_map.get(iid) == category_id}
        if not raw_material_ids:
            print(f"[RESOLVER] No category-{category_id} items with CBR at '{location_name}' — using fallback")
            return _FALLBACK.copy()

        qcp_map = _fetch_qcp_map(client, raw_material_ids)
        # Intersection: items with category + CBR + QCP
        qualified_ids = list(raw_material_ids & set(qcp_map.keys()))

        if not qualified_ids:
            print(f"[RESOLVER] No items with both CBR + QCP at '{location_name}' — using fallback")
            return _FALLBACK.copy()

        item_id = random.choice(qualified_ids)
        item_name = item_map[item_id]
        cbr = cbr_map[item_id]
        rate = round(random.uniform(cbr["min"], cbr["max"]), 2)
        quantity = random.randint(_QTY_MIN, _QTY_MAX)
        cqp_params = qcp_map[item_id]
        per_bag_weight = round(quantity * 0.04, 2)

        print(
            f"[RESOLVER] item='{item_name}' category_id={category_id} "
            f"qty={quantity} rate={rate} qcp_rows={len(cqp_params)} per_bag_weight={per_bag_weight}"
        )
        return {
            "item_name": item_name,
            "quantity": quantity,
            "rate": rate,
            "cqp_params": cqp_params,
            "per_bag_weight": per_bag_weight,
        }
    except Exception as exc:
        print(f"[RESOLVER] Error: {exc} — using fallback")
        return _FALLBACK.copy()

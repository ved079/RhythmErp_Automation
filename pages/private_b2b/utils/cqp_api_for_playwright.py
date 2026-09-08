"""
cqp_api_for_playwright.py
--------------------------
Fetches Commodity Quality Parameter (CQP) configs via the ERP API for use in
Playwright test scripts — without visiting the CQP screen in the browser.

What it does:
  1. Sniffs the Bearer token + tenant ID from an already-logged-in Playwright page
     by intercepting one outgoing API request (no second login needed).
  2. Uses RhythmERPAPIClient to call the CQP API and resolve min/max quality
     values for a given list of item names.
  3. Returns a cqp_config dict in the exact shape that QCPlaywrightPage.fill_qc_params_safe
     and fill_qc_params_popup expect:
       { item_name: [{"param": str, "min_q": float, "max_q": float,
                      "multiplier": float, "is_pct": bool}] }

Intended use:
  Call build_cqp_config(item_names, page) before opening the QC form in any
  Playwright test. Set the result on the QC page object:
      qc.cqp_config  = cqp_config
      qc.item_names  = item_names
  This ensures fill_qc_params_safe uses real ERP values instead of guessing 1.

Reusable across all Playwright flows (PO→QC→PB, GP→GRN→QC, etc.).
Just import build_cqp_config wherever a QC form is filled.
"""

import re
from typing import Dict, List, Optional

from common.erp_api_client import RhythmERPAPIClient


# ── Token sniffing ────────────────────────────────────────────────────────────

def sniff_token_from_page(page) -> tuple:
    """Capture Bearer token + tenant ID from the live Playwright page.

    Triggers a lightweight navigation to force one outgoing API request, then
    reads the Authorization and x-tenant-id headers from it.

    Returns:
        (token: str, tenant_id: str)  — token is WITHOUT the "Bearer " prefix.

    Raises:
        RuntimeError if the token cannot be captured.
    """
    captured = {}

    def _handle_request(request):
        if captured:
            return
        auth = request.headers.get("authorization", "")
        tenant = request.headers.get("x-tenant-id", "")
        if auth.startswith("Bearer ") and tenant:
            captured["token"]     = auth.replace("Bearer ", "").strip()
            captured["tenant_id"] = tenant.strip()

    page.on("request", _handle_request)
    try:
        # Trigger any navigation that hits the ERP API — reload is the safest
        page.reload()
        page.wait_for_timeout(3000)
    finally:
        page.remove_listener("request", _handle_request)

    if not captured:
        raise RuntimeError(
            "Could not capture Bearer token from Playwright page. "
            "Make sure the page is logged in and making API requests."
        )

    return captured["token"], captured["tenant_id"]


# ── Item name → ref_id resolution ─────────────────────────────────────────────

def _resolve_item_ref_ids(client: RhythmERPAPIClient, item_names: List[str]) -> Dict[str, int]:
    """Return {item_name: item_ref_id} for the given item names.

    Searches the Item master listing for each name and picks the first exact match.
    """
    name_to_id: Dict[str, int] = {}
    for name in item_names:
        if not name:
            continue
        try:
            resp = client.list_entries("Item Master", page=1, page_size=50, search=name)
            rows = (resp or {}).get("screenmatlistingdata_set") or []
            for row in rows:
                # Item Master listing returns id/name/code/uom/status
                row_name = str(row.get("name") or "").strip()
                if row_name.lower() == name.lower() or not name_to_id.get(name):
                    ref_id = row.get("id")
                    if ref_id:
                        name_to_id[name] = int(ref_id)
                        if row_name.lower() == name.lower():
                            break
        except Exception as e:
            print(f"[CQP-API] Could not resolve item_ref_id for '{name}': {e}")
    return name_to_id


# ── Quality Parameter ID → name resolution ────────────────────────────────────

def _resolve_quality_param_names(client: RhythmERPAPIClient) -> Dict[int, str]:
    """Return {quality_param_id: name} from the Quality Parameter Master screen."""
    id_to_name: Dict[int, str] = {}
    try:
        resp = client.list_entries("Quality Parameter Master", page=1, page_size=500)
        rows = (resp or {}).get("screenmatlistingdata_set") or []
        for row in rows:
            ref_id = row.get("id")
            name   = str(row.get("name") or row.get("quality_parameter") or "").strip()
            if ref_id and name:
                id_to_name[int(ref_id)] = name
        print(f"[CQP-API] Quality Parameter Master: {len(id_to_name)} entries loaded")
    except Exception as e:
        print(f"[CQP-API] Could not load Quality Parameter Master: {e}")
    return id_to_name


# ── CQP param resolution ──────────────────────────────────────────────────────

def _fetch_cqp_for_item(client: RhythmERPAPIClient, item_ref_id: int,
                        qp_names: Dict[int, str] = None) -> List[dict]:
    """Fetch CQP rows for one item_ref_id via the API.

    Returns list of param dicts in the shape QCPlaywrightPage expects:
        [{"param": str, "min_q": float, "max_q": float,
          "multiplier": float, "is_pct": bool}]
    Returns [] if no CQP entry exists for this item.
    """
    try:
        resp = client.list_entries("Commodity Quality Parameter", page=1, page_size=500)
        rows = (resp or {}).get("screenmatlistingdata_set") or []
    except Exception as e:
        print(f"[CQP-API] Failed to list CQP entries: {e}")
        return []

    for row in rows:
        entry_id = row.get("id")
        if not entry_id:
            continue
        try:
            detail = client.get_entry("Commodity Quality Parameter", entry_id)
        except Exception:
            continue
        if not detail:
            continue
        if detail.get("item_ref_id") != item_ref_id:
            continue

        # Found the entry for this item — parse children → details.
        # Group by quality_type and keep the lowest min_quality_value per param
        # (CQP can have multiple rows per param with different grade ranges).
        qp_names = qp_names or {}
        grouped = {}  # quality_type_id → {"param": name, "min_q": float, "max_q": float, ...}

        def _f(v):
            try:
                return float(v) if v not in (None, "", "null") else None
            except (TypeError, ValueError):
                return None

        children = detail.get("children") or []
        for child in children:
            for p in (child.get("details") or []):
                quality_type_id = p.get("quality_type")
                if quality_type_id is None:
                    continue
                qt_key = int(quality_type_id)

                if qt_key in qp_names:
                    param_label = qp_names[qt_key]
                else:
                    raw_label = (
                        p.get("quality_parameter") or p.get("quality_param")
                        or p.get("param") or p.get("name") or str(qt_key)
                    )
                    param_label = str(raw_label).strip()
                if not param_label:
                    continue

                min_q  = _f(p.get("min_quality_value"))
                max_q  = _f(p.get("max_quality_value"))
                mult   = _f(p.get("multiplier"))
                is_pct = bool(p.get("is_rate_percentage") or p.get("is_pct"))
                min_q  = min_q if min_q is not None else 1.0
                max_q  = max_q if max_q is not None else 100.0
                mult   = mult  if mult  is not None else 1.0

                if qt_key not in grouped:
                    grouped[qt_key] = {
                        "param": param_label, "min_q": min_q,
                        "max_q": max_q, "multiplier": mult, "is_pct": is_pct,
                    }
                else:
                    # Keep the lowest min_q across all rows for this param
                    if min_q < grouped[qt_key]["min_q"]:
                        grouped[qt_key]["min_q"] = min_q

        params = list(grouped.values())
        print(f"[CQP-API] item_ref_id={item_ref_id} → {[p['param'] + '=' + str(p['min_q']) for p in params]}")
        return params

    print(f"[CQP-API] No CQP entry found for item_ref_id={item_ref_id}")
    return []


# ── Public API ────────────────────────────────────────────────────────────────

def build_cqp_config(item_names: List[str], page) -> Dict[str, List[dict]]:
    """Main entry point. Given a list of item names and a logged-in Playwright page,
    returns a cqp_config dict ready to set on QCPlaywrightPage.

    Usage in any Playwright test:
        from pages.private_b2b.utils.cqp_api_for_playwright import build_cqp_config

        cqp_config = build_cqp_config([item_name], logged_in_page)
        qc.cqp_config = cqp_config
        qc.item_names = [item_name]
        qc.fill_qc_params_safe(row_index=0)

    Returns:
        { item_name: [{"param": str, "min_q": float, "max_q": float,
                       "multiplier": float, "is_pct": bool}] }
        Items with no CQP entry map to [].
    """
    token, tenant_id = sniff_token_from_page(page)

    client = RhythmERPAPIClient()
    client.login_from_browser(token=token, tenant_id=tenant_id)

    name_to_ref_id = _resolve_item_ref_ids(client, item_names)
    qp_names       = _resolve_quality_param_names(client)

    cqp_config: Dict[str, List[dict]] = {}
    for name in item_names:
        ref_id = name_to_ref_id.get(name)
        if ref_id is None:
            print(f"[CQP-API] No item_ref_id found for '{name}' — will fall back to default values")
            cqp_config[name] = []
            continue
        cqp_config[name] = _fetch_cqp_for_item(client, ref_id, qp_names=qp_names)

    return cqp_config

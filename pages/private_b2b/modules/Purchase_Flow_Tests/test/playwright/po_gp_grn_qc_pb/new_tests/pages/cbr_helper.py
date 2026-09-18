"""
CBR rate resolver — fetches Commodity Base Rate min/max for an item at a
location by display name, then returns a random rate within that range.

Falls back to a wide random range (500–6000) when no CBR entry is found.
"""

import random
import sys
import os

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from common.erp_api_client import RhythmERPAPIClient

_FALLBACK_MIN = 500.0
_FALLBACK_MAX = 6000.0

EMAIL     = "kedar@rhythmflows.com"
PASSWORD  = "Kedar@999999"
TENANT_ID = "666"  # Jay Kisan Ltd tenant ID


def _make_client() -> RhythmERPAPIClient:
    client = RhythmERPAPIClient(username=EMAIL, password=PASSWORD, tenant_id=TENANT_ID)
    client.login()
    return client


def _resolve_item_id(client: RhythmERPAPIClient, item_name: str) -> int | None:
    resp = client.list_entries("Item Master", page_size=500)
    rows = (resp or {}).get("screenmatlistingdata_set") or (resp or {}).get("results") or []
    for row in rows:
        if str(row.get("name") or "").strip() == item_name:
            return int(row["id"])
    return None


def _resolve_location_id(client: RhythmERPAPIClient, location_name: str) -> int | None:
    resp = client.list_entries("Location", page_size=500)
    rows = (resp or {}).get("screenmatlistingdata_set") or (resp or {}).get("results") or []
    for row in rows:
        if str(row.get("name") or "").strip() == location_name:
            return int(row["id"])
    return None


def _fetch_cbr_range(client: RhythmERPAPIClient, item_id: int, location_id: int) -> dict | None:
    """Return {"min": float, "max": float} from CBR for item at location, or None."""
    listing = client.list_entries("Commodity Base Rate", page_size=500)
    entries = (listing or {}).get("screenmatlistingdata_set") or (listing or {}).get("results") or []
    for e in entries:
        try:
            detail = client.get_entry("Commodity Base Rate", e["id"])
            if not detail:
                continue
            if int(detail.get("location_ref_id") or 0) != location_id:
                continue
            for child in detail.get("children", []):
                for row in child.get("details", []):
                    if int(row.get("item_ref_id") or 0) != item_id:
                        continue
                    mn = row.get("minimum_range")
                    mx = row.get("maximum_range")
                    if mn is not None and mx is not None:
                        return {"min": float(mn), "max": float(mx)}
        except Exception:
            continue
    return None


def get_random_rate(item_name: str, location_name: str) -> float:
    """
    Resolve item and location by name, fetch CBR min/max, return random rate.
    Falls back to uniform(500, 6000) if CBR not found.
    """
    try:
        client = _make_client()
        item_id = _resolve_item_id(client, item_name)
        if item_id is None:
            raise ValueError(f"Item '{item_name}' not found in Item Master")
        location_id = _resolve_location_id(client, location_name)
        if location_id is None:
            raise ValueError(f"Location '{location_name}' not found")
        cbr = _fetch_cbr_range(client, item_id, location_id)
        if cbr:
            rate = round(random.uniform(cbr["min"], cbr["max"]), 2)
            print(f"[CBR] {item_name} @ {location_name}: range [{cbr['min']}, {cbr['max']}] → rate={rate}")
            return rate
        else:
            rate = round(random.uniform(_FALLBACK_MIN, _FALLBACK_MAX), 2)
            print(f"[CBR] No entry found for '{item_name}' @ '{location_name}' — fallback rate={rate}")
            return rate
    except Exception as exc:
        rate = round(random.uniform(_FALLBACK_MIN, _FALLBACK_MAX), 2)
        print(f"[CBR] Error resolving rate: {exc} — fallback rate={rate}")
        return rate

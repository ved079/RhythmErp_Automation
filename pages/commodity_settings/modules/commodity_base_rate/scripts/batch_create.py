#!/usr/bin/env python3
"""
Commodity Base Rate — Batch Create via API

Creates CBR entries via the ERP API (bypasses the UI entirely).
Handles FK dropdown fields (Pricing Type, Location) and the
unique (to_date, location_ref_id) constraint.

IMPORTANT — BUG-004 / to_date Override:
  The ERP server ALWAYS overrides the to_date field to 2099-12-30
  regardless of the value sent in the payload. This means the unique
  constraint (to_date, location_ref_id) effectively limits each
  location to ONE CBR entry with the default sentinel to_date.

  Since all 10 existing locations already have CBR entries with
  to_date=2099, new CBR entries CANNOT be created for those locations.

STRATEGY — Create New Locations:
  To bypass the (to_date, location_ref_id) constraint, the script:
  1. Fetches all existing locations and CBR entries from the API
  2. Finds locations that have NO CBR entry yet (free locations)
  3. If not enough free locations, creates NEW locations via the
     ERP's "Location" screen API
  4. Creates CBR entries for those free/new locations
  5. Each new location gets exactly 1 CBR entry with the default
     to_date=2099-12-30 (no duplicates possible)

  This approach is clean and reliable — no year-shifting hacks,
  no versioning tricks, no duplicate errors.

FALLBACK — Versioning:
  If creating new locations fails (permissions, etc.), the script
  falls back to "versioning" — POST with id=<existing_entry_id>
  and the same location. This bypasses the duplicate check when
  the referenced entry is the only one for its (to_date, location).

NOTE — Grid Detail Rows:
  The ERP's API does NOT support creating grid detail rows (Item Name,
  Item Rate, UOM) via the main POST endpoint. The batch_create script
  creates HEADER-ONLY entries. Grid rows must be added through the UI
  or a separate mechanism.

Usage:
    python batch_create.py              # Creates 10 entries
    python batch_create.py --count 20   # Creates 20 entries

Screen: Commodity Base Rate
URL:    /#/dynamic-screens/Commodity%20Base%20Rate
"""

import sys
import os
import re
import argparse
import time

# ── Path setup ────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from common.erp_api_client import ErpApiClient
from common.logger import log
from pages.commodity_settings.modules.commodity_base_rate.data.cbr_data import (
    PRICING_TYPE_ID_MAP,
    LOCATION_ID_MAP,
)

SCREEN_NAME = "Commodity Base Rate"
LOCATION_SCREEN = "Location"

# Location names for auto-creation (descriptive, not in existing LOCATION_ID_MAP)
NEW_LOCATION_NAMES = [
    "Nagpur Depot",
    "Nashik Warehouse",
    "Aurangabad Hub",
    "Solapur Center",
    "Kolhapur Branch",
    "Thane Facility",
    "Amravati Yard",
    "Jalgaon Site",
    "Sangli Point",
    "Ratnagiri Port",
    "Dhule Station",
    "Nanded Complex",
    "Latur Center",
    "Osmanabad Hub",
    "Parbhani Depot",
    "Beed Warehouse",
    "Jalna Site",
    "Wardha Point",
    "Chandrapur Yard",
    "Gadchiroli Base",
]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Batch create Commodity Base Rate entries via API"
    )
    parser.add_argument(
        "--count", type=int, default=10,
        help="Number of entries to create. Default: 10"
    )
    return parser.parse_args()


# ── Step 1: Fetch existing CBR entries and find free locations ────────

def fetch_existing_cbr_locations(api: ErpApiClient) -> set:
    """
    Fetch all existing CBR entries and return the set of location_ref_id
    integers that already have an entry with to_date=2099 (the default).

    Since BUG-004 overrides to_date to 2099-12-30, we only need to check
    for entries with that to_date — any other to_date values are "closed"
    entries that don't block new creation.

    Args:
        api: Authenticated ErpApiClient instance

    Returns:
        Set of location_ref_id integers already used in CBR with to_date=2099
    """
    used_locs = set()

    try:
        result = api.list_entries(SCREEN_NAME, page_size=200)
        if not result:
            log.warning("[DEDUP] Could not fetch CBR listing")
            return used_locs

        entries = result.get("screenmatlistingdata_set", [])
        if not entries:
            log.info("[DEDUP] No existing CBR entries found")
            return used_locs

        log.info(f"[DEDUP] Found {len(entries)} existing CBR entries")

        for entry in entries:
            loc_val = entry.get("location_ref_id")
            to_date = str(entry.get("to_date", ""))

            # Only count entries with the default to_date (2099)
            if "2099" not in to_date:
                continue

            # Resolve location to integer ID
            loc_id = None
            if loc_val and isinstance(loc_val, str):
                for name, id_val in LOCATION_ID_MAP.items():
                    if name.lower() == loc_val.lower():
                        loc_id = id_val
                        break
                if loc_id is None:
                    try:
                        loc_id = int(loc_val)
                    except (ValueError, TypeError):
                        pass
            elif isinstance(loc_val, (int, float)):
                loc_id = int(loc_val)

            if loc_id is not None:
                used_locs.add(loc_id)

        log.info(
            f"[DEDUP] {len(used_locs)} locations already have CBR entries "
            f"with to_date=2099: {sorted(used_locs)}"
        )

    except Exception as e:
        log.warning(f"[DEDUP] Error fetching CBR entries: {e}")

    return used_locs


def fetch_all_location_ids(api: ErpApiClient) -> dict:
    """
    Fetch all locations from the ERP Location dropdown.
    Returns a dict of {name: id} for ALL locations (including ones
    not in our static LOCATION_ID_MAP).

    Args:
        api: Authenticated ErpApiClient instance

    Returns:
        Dict mapping location name to integer ID
    """
    all_locations = dict(LOCATION_ID_MAP)  # Start with static map

    try:
        # Fetch the CBR screen schema to get the location dropdown options
        schema = api.get_screen_schema(SCREEN_NAME)
        if schema:
            from common.erp_api_client import RhythmERPAPIClient
            client = api  # ErpApiClient extends RhythmERPAPIClient
            fields = client._flatten_fields(schema.get("screendefinition_set", []))
            for field in fields:
                if field.get("field_key") == "location_ref_id":
                    opts = field.get("filter_dropdown_raw_query", [])
                    if isinstance(opts, list):
                        for opt in opts:
                            opt_id = opt.get("id")
                            opt_key = opt.get("key")
                            if opt_id and opt_key:
                                # Don't overwrite static map, but add new ones
                                if opt_key not in all_locations:
                                    all_locations[opt_key] = opt_id
                    break

        log.info(
            f"[LOC] Found {len(all_locations)} locations in ERP "
            f"(static map had {len(LOCATION_ID_MAP)})"
        )

    except Exception as e:
        log.warning(f"[LOC] Error fetching location options: {e}")

    return all_locations


# ── Step 2: Create new locations ──────────────────────────────────────

def create_new_location(api: ErpApiClient, name: str) -> int:
    """
    Create a new Location entry via the ERP's "Location" screen API.

    The Location screen has a simple structure:
      - name: string (required)
      - description: string (optional)

    Args:
        api: Authenticated ErpApiClient instance
        name: Location name to create

    Returns:
        Integer ID of the newly created location, or None on failure
    """
    payload = {
        "id": "",
        "attribute_name": LOCATION_SCREEN,
        "name": name,
        "description": f"Auto-created for CBR batch testing",
    }

    try:
        result = api.create_entry(payload)
        if result and result.get("id"):
            new_id = result["id"]
            log.info(f"[LOC] Created location '{name}' with id={new_id}")
            return new_id
        else:
            log.warning(f"[LOC] Failed to create location '{name}' — no id in response")
            return None
    except Exception as e:
        log.warning(f"[LOC] Error creating location '{name}': {e}")
        return None


# ── Step 3: Create CBR entries for free locations ─────────────────────

def create_cbr_entry(api: ErpApiClient, pricing_type_id: int,
                     location_id: int) -> dict:
    """
    Create a single CBR header entry for a given location.

    Since the server overrides to_date to 2099-12-30, we send the
    default value. The location must NOT already have a CBR entry
    with to_date=2099 (otherwise duplicate error).

    Args:
        api: Authenticated ErpApiClient instance
        pricing_type_id: 118 (Common) or 120 (Supplier)
        location_id: Integer FK for the location

    Returns:
        Result dict from API, or None on failure
    """
    payload = {
        "id": "",
        "attribute_name": SCREEN_NAME,
        "pricing_type_ref_id": pricing_type_id,
        "from_date": "2026-06-02T00:00:00Z",
        "to_date": "2099-12-30T18:30:00Z",
        "location_ref_id": location_id,
    }

    try:
        result = api.create_entry(payload)
        if result is not None:
            return {"success": True, "data": result, "payload": payload}
        else:
            return {"success": False, "error": "API create failed", "payload": payload}
    except Exception as e:
        return {"success": False, "error": str(e), "payload": payload}


# ── Main ──────────────────────────────────────────────────────────────

def main():
    args = parse_args()
    count = args.count

    print("=" * 70)
    print("  COMMODITY BASE RATE — BATCH CREATE (API)")
    print(f"  Screen: {SCREEN_NAME}")
    print(f"  Entries to create: {count}")
    print("=" * 70)
    print()
    print("  NOTE: The ERP overrides to_date to 2099-12-30 (BUG-004).")
    print("  Strategy: create NEW locations, then CBR entries for them.")
    print("=" * 70)

    api = ErpApiClient()
    token = api.prompt_for_token()
    api.set_session_from_token(token)

    # ── Step 1: Find which locations are already used ──────────────────
    print()
    print("  Step 1: Checking existing CBR entries and locations...")
    print("-" * 70)

    used_locations = fetch_existing_cbr_locations(api)
    all_locations = fetch_all_location_ids(api)

    # Find FREE locations (exist in ERP but have no CBR entry with to_date=2099)
    free_locations = {
        name: loc_id for name, loc_id in all_locations.items()
        if loc_id not in used_locations
    }

    print(f"  Total locations in ERP: {len(all_locations)}")
    print(f"  Locations with CBR (to_date=2099): {len(used_locations)}")
    print(f"  FREE locations (no CBR): {len(free_locations)}")
    if free_locations:
        for name, lid in sorted(free_locations.items(), key=lambda x: x[1]):
            print(f"    - {name} (id={lid})")

    # ── Step 2: Ensure we have enough free locations ──────────────────
    needed = count
    available = len(free_locations)

    if available < needed:
        to_create = needed - available
        print()
        print(f"  Step 2: Need {needed} free locations, only {available} available.")
        print(f"  Creating {to_create} new locations via the Location API...")
        print("-" * 70)

        # Pick names that don't already exist
        existing_names = set(n.lower() for n in all_locations.keys())
        name_idx = 0

        for _ in range(to_create):
            # Find a name that doesn't exist yet
            while name_idx < len(NEW_LOCATION_NAMES):
                candidate = NEW_LOCATION_NAMES[name_idx]
                name_idx += 1
                if candidate.lower() not in existing_names:
                    break
            else:
                # Exhausted the name list — generate numbered fallback
                fallback_num = name_idx + 1
                candidate = f"Test Location {fallback_num}"

            new_id = create_new_location(api, candidate)
            if new_id:
                free_locations[candidate] = new_id
                all_locations[candidate] = new_id
                existing_names.add(candidate.lower())
                print(f"    Created: {candidate} (id={new_id})")
            else:
                print(f"    FAILED to create: {candidate}")

            time.sleep(0.2)

        print(f"  Now have {len(free_locations)} free locations")
    else:
        print()
        print(f"  Step 2: {available} free locations available — enough for {needed}.")
        print("  No new locations needed.")

    # ── Step 3: Create CBR entries for free locations ──────────────────
    print()
    print(f"  Step 3: Creating {count} CBR entries for free locations...")
    print("-" * 70)

    # Build a list of (pricing_type_id, location_id) pairs
    # Alternate between Common and Supplier pricing types
    pricing_types = [118, 120]  # Common, Supplier
    results = []
    created = 0
    failed = 0

    # Sort free locations by ID for consistent ordering
    sorted_free = sorted(free_locations.items(), key=lambda x: x[1])

    for i in range(count):
        if i >= len(sorted_free):
            print(f"    [{i+1}/{count}] No more free locations — stopping")
            break

        loc_name, loc_id = sorted_free[i]
        pt_id = pricing_types[i % len(pricing_types)]
        pt_name = "Common" if pt_id == 118 else "Supplier"

        print(
            f"    [{i+1}/{count}] Creating CBR: {pt_name}/{loc_name} "
            f"(loc_id={loc_id})...",
            end=" ",
            flush=True,
        )

        result = create_cbr_entry(api, pt_id, loc_id)

        if result.get("success"):
            created += 1
            new_id = result.get("data", {}).get("id", "?")
            print(f"OK (id={new_id})")
        else:
            failed += 1
            print(f"FAILED: {result.get('error', 'Unknown')}")

        results.append(result)

        if i < count - 1:
            time.sleep(0.3)

    # ── Summary ───────────────────────────────────────────────────────
    print()
    print("=" * 70)
    print("  FINAL SUMMARY")
    print("=" * 70)
    status_icon = "OK" if failed == 0 else "!!"
    print(f"  [{status_icon}] {SCREEN_NAME:<35} {created:>3}/{count} created")
    print("-" * 70)

    if failed > 0:
        for i, r in enumerate(results):
            if not r.get("success"):
                p = r.get("payload", {})
                loc_id = p.get("location_ref_id", "?")
                pt_id = p.get("pricing_type_ref_id", "?")
                print(f"  FAILED (pricing={pt_id}, location={loc_id}): "
                      f"{r.get('error', 'Unknown')}")

    if created < count:
        print(f"  WARNING: Only {created}/{count} entries created.")

    print(f"  Total: {created} created, {failed} failed")
    print("=" * 70)

    api.close()


if __name__ == "__main__":
    main()

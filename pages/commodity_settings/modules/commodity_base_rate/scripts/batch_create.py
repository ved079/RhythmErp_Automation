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
  location to ONE CBR entry total (since all to_dates collapse to
  2099-12-30 in the database).

STRATEGY — Create New Locations:
  To bypass the (to_date, location_ref_id) constraint, the script:
  1. Fetches ALL locations from the ERP dropdown (via screen schema)
  2. Fetches ALL existing CBR entries and determines which locations
     already have entries (dedup)
  3. Finds locations that have NO CBR entry yet (free locations)
  4. If not enough free locations, creates NEW locations via the
     ERP's "Location" screen API
  5. Creates CBR entries for those free/new locations
  6. Each new location gets exactly 1 CBR entry with the default
     to_date=2099-12-30 (no duplicates possible)

DEDUP FIX (v3 — 2026-06-02):
  Previous versions had two bugs:
    BUG-A: fetch_existing_cbr_locations() used only the static
           LOCATION_ID_MAP (10 entries) for name resolution.
           Locations 11-20 (auto-created by previous runs) were
           NOT in the map, so the dedup couldn't resolve their
           names to IDs and silently skipped them — making those
           locations appear "free" when they were actually occupied.
    BUG-B: The dedup filtered entries by to_date containing "2099".
           Since BUG-004 overrides ALL to_dates to 2099-12-30 in
           the database, ANY existing CBR entry blocks new creation,
           regardless of what the listing displays. The filter was
           incorrectly excluding some entries.

  Fix: Use the FULL all_locations dict (fetched from screen schema
  dropdown) for name resolution, remove the to_date filter, and add
  a detail-fetch fallback for entries where name resolution fails.

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
import random
import time

# ── Path setup ────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from common.erp_api_client import ErpApiClient
from common.fk_resolver import FkResolver
from common.logger import log
from pages.commodity_settings.modules.commodity_base_rate.data.cbr_data import (
    PRICING_TYPE_ID_MAP,
    LOCATION_ID_MAP,
    ITEM_ID_MAP,
    UOM_ID_MAP,
    CBR_GRID_DATA,
)

SCREEN_NAME = "Commodity Base Rate"
LOCATION_SCREEN = "Location"

# FK fields that need resolution from live ERP
FK_SCREEN_MAP = {
    "location_ref_id": "Location",
    "item_ref_id": "Item Master",
    "uom": "UOM",
}

# Location names for auto-creation (descriptive, not in existing LOCATION_ID_MAP)
NEW_LOCATION_NAMES = [
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
    "Washim Depot",
    "Hingoli Warehouse",
    "Buldhana Center",
    "Akot Hub",
    "Wani Site",
    "Ballarpur Point",
    "Umred Yard",
    "Bhandara Base",
    "Gondia Port",
]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Batch create Commodity Base Rate entries via API"
    )
    parser.add_argument(
        "--count", type=int, default=None,
        help="Number of entries to create (omit to prompt)"
    )
    parser.add_argument("--token", default=None, help="ERP Bearer token (omit to prompt)")
    parser.add_argument("--tenant", default=None, help="Tenant ID (omit to prompt)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be created without sending")
    return parser.parse_args()


# ── Step 1: Fetch all locations from the ERP ─────────────────────────

def fetch_all_location_ids(api: ErpApiClient) -> dict:
    """
    Fetch all locations from the ERP Location dropdown.

    Uses the CBR screen schema's filter_dropdown_raw_query to get
    ALL location options with their IDs. This is the MOST RELIABLE
    way to get the complete {name: id} map because the dropdown
    always returns {id: int, key: name} pairs directly.

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


# ── Step 2: Fetch existing CBR entries and find free locations ────────

def fetch_existing_cbr_locations(api: ErpApiClient, all_locations: dict = None) -> set:
    """
    Fetch ALL existing CBR entries and return the set of location_ref_id
    integers that already have a CBR entry.

    Since BUG-004 overrides to_date to 2099-12-30 for ALL entries,
    ANY existing CBR entry for a location blocks new creation.
    We consider ALL entries as blocking, regardless of their displayed
    to_date value.

    Name resolution uses the full all_locations dict (fetched from the
    CBR screen schema dropdown), not just the static LOCATION_ID_MAP.
    This correctly resolves auto-created locations (like "Nagpur Depot",
    "Nashik Warehouse") that aren't in the static map.

    If name resolution fails for some entries, falls back to fetching
    detailed entries via get_entry() which returns integer FK IDs.

    Args:
        api: Authenticated ErpApiClient instance
        all_locations: Dict of {name: id} for ALL locations from
                       fetch_all_location_ids(). Used for name resolution.

    Returns:
        Set of location_ref_id integers already used in CBR
    """
    used_locs = set()

    # Build a reverse map: lowercase name -> ID, for fast lookup
    loc_name_to_id = {}
    if all_locations:
        for name, lid in all_locations.items():
            loc_name_to_id[name.lower().strip()] = lid

    try:
        # Fetch ALL CBR entries with pagination
        all_entries = []
        page = 1
        while True:
            result = api.list_entries(SCREEN_NAME, page=page, page_size=200)
            if not result:
                break

            entries = result.get("screenmatlistingdata_set", [])
            if not entries:
                break

            all_entries.extend(entries)

            # Check if there are more pages
            # The ERP listing API doesn't always provide pagination metadata.
            # If we got fewer entries than page_size, we've reached the end.
            if len(entries) < 200:
                break

            page += 1
            time.sleep(0.1)  # Small delay between pages

        if not all_entries:
            log.info("[DEDUP] No existing CBR entries found")
            return used_locs

        log.info(f"[DEDUP] Found {len(all_entries)} existing CBR entries (all pages)")

        # Strategy 1: Resolve location names from listing using all_locations dict
        unresolved_entries = []  # Track entries we couldn't resolve

        for entry in all_entries:
            loc_val = entry.get("location_ref_id")

            loc_id = None

            # Try resolving using all_locations dict (full set from dropdown)
            if loc_val is not None:
                if isinstance(loc_val, str):
                    # Try matching against all_locations names (case-insensitive)
                    loc_id = loc_name_to_id.get(loc_val.lower().strip())

                    # Fallback to static LOCATION_ID_MAP
                    if loc_id is None:
                        for name, id_val in LOCATION_ID_MAP.items():
                            if name.lower() == loc_val.lower():
                                loc_id = id_val
                                break

                    # Try parsing as integer
                    if loc_id is None:
                        try:
                            loc_id = int(loc_val)
                        except (ValueError, TypeError):
                            pass

                elif isinstance(loc_val, (int, float)):
                    loc_id = int(loc_val)

            if loc_id is not None:
                used_locs.add(loc_id)
            else:
                # Track this entry for Strategy 2 (detail-fetch fallback)
                entry_id = entry.get("id")
                if entry_id is not None:
                    unresolved_entries.append(entry_id)

        if unresolved_entries:
            log.info(
                f"[DEDUP] {len(unresolved_entries)} entries had unresolvable "
                f"location names — fetching details..."
            )

            # Strategy 2: Fetch detailed entries to get integer FK IDs
            # (like the CQP script's fallback)
            for i, entry_id in enumerate(unresolved_entries[:50]):  # Cap at 50
                try:
                    detail = api.get_entry(SCREEN_NAME, entry_id)
                    if detail and "location_ref_id" in detail:
                        raw_loc_id = detail["location_ref_id"]
                        try:
                            used_locs.add(int(raw_loc_id))
                        except (ValueError, TypeError):
                            log.warning(
                                f"[DEDUP] Could not parse location_ref_id "
                                f"from detail entry {entry_id}: {raw_loc_id}"
                            )
                except Exception as e:
                    log.warning(f"[DEDUP] Error fetching detail {entry_id}: {e}")

                if i > 0 and i % 10 == 0:
                    time.sleep(0.2)  # Small delay to avoid rate limiting

        log.info(
            f"[DEDUP] {len(used_locs)} locations already have CBR entries: "
            f"{sorted(used_locs)}"
        )

    except Exception as e:
        log.warning(f"[DEDUP] Error fetching CBR entries: {e}")

    return used_locs


# ── Step 3: Create new locations ──────────────────────────────────────

def discover_location_screen_structure(api: ErpApiClient) -> dict:
    """
    Discover the Location screen's payload structure by fetching
    an existing entry and examining its fields.

    Returns:
        Dict with the minimal required payload template, or a default
        template if discovery fails.
    """
    try:
        # Try to fetch the Location screen schema
        schema = api.get_screen_schema(LOCATION_SCREEN)
        if schema:
            fields = api._flatten_fields(schema.get("screendefinition_set", []))
            required_fields = {}
            for field in fields:
                if field.get("is_mandatory") or field.get("required"):
                    key = field.get("field_key")
                    if key and key not in ("id", "attribute_name"):
                        required_fields[key] = field.get("field_type", "string")
            if required_fields:
                log.info(f"[LOC-SCHEMA] Required fields: {list(required_fields.keys())}")
                return required_fields
    except Exception as e:
        log.warning(f"[LOC-SCHEMA] Could not fetch Location schema: {e}")

    # Default template based on common Location screen structure
    return {"name": "string"}


def create_new_location(api: ErpApiClient, name: str) -> int:
    """
    Create a new Location entry via the ERP's "Location" screen API.

    The Location screen typically has a simple structure:
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
            log.warning(
                f"[LOC] Failed to create location '{name}' — "
                f"no id in response: {result}"
            )
            return None
    except Exception as e:
        log.warning(f"[LOC] Error creating location '{name}': {e}")
        return None


# ── Step 4: Create CBR entries for free locations ─────────────────────

def create_cbr_entry(api: ErpApiClient, pricing_type_id: int,
                     location_id: int, item_map: dict,
                     uom_list: list) -> dict:
    """
    Create a single CBR header entry with one detail row per item.

    For each item in item_map, adds a detail row with:
      - item_ref_id: the item's FK ID
      - uom: a randomly chosen UOM FK ID from uom_list
      - item_rate: a random integer between 500 and 5000

    Args:
        api: Authenticated ErpApiClient instance
        pricing_type_id: FK for Pricing Type
        location_id: FK for Location
        item_map: {item_name: item_id} — all live items from FkResolver
        uom_list: list of UOM FK IDs to pick from randomly

    Returns:
        Result dict: {"success": bool, "data": ..., "error": ..., "payload": ...}
    """
    detail_rows = []
    for item_name, item_id in item_map.items():
        uom_id = random.choice(uom_list) if uom_list else None
        min_range = round(random.uniform(500, 2000), 2)
        max_range = round(random.uniform(5000, 10000), 2)
        row = {
            "item_ref_id": item_id,
            "minimum_range": min_range,
            "maximum_range": max_range,
            "details": [],
        }
        if uom_id is not None:
            row["uom"] = uom_id
        detail_rows.append(row)

    payload = {
        "id": "",
        "attribute_name": SCREEN_NAME,
        "pricing_type_ref_id": pricing_type_id,
        "from_date": "2026-06-02T00:00:00Z",
        "to_date": "2099-12-30T18:30:00Z",
        "location_ref_id": location_id,
        "details": [],
        "children": [
            {
                "stepper_name": "Define Item Rate Details",
                "is_stepper": True,
                "details": detail_rows,
                "children": [],
            }
        ],
    }

    try:
        result = api.create_entry(payload)
        if result is not None:
            return {"success": True, "data": result, "payload": payload}
        else:
            return {"success": False, "error": "API create failed", "payload": payload}
    except Exception as e:
        return {"success": False, "error": str(e), "payload": payload}


# ── FK Resolution ──────────────────────────────────────────────────

def resolve_all_fk_ids(resolver):
    """Resolve all CBR FK IDs from the live ERP."""
    fk_ids = {}
    for field, screen in FK_SCREEN_MAP.items():
        try:
            resolved = resolver.resolve(screen)
            if resolved:
                print(f"    {field}: {len(resolved)} options found from '{screen}'")
                samples = list(resolved.items())[:3]
                for name, fid in samples:
                    print(f"      {name}: {fid}")
                fk_ids[field] = resolved
            else:
                print(f"    {field}: NOT FOUND — will fall back to hardcoded IDs")
        except Exception as e:
            print(f"    {field}: ERROR — {e}")
    return fk_ids


# ── Main ──────────────────────────────────────────────────────────────

def prompt_missing_args(args):
    if not args.token:
        print("\n  No token provided. Open DevTools -> Network -> any /core/ request -> Authorization header")
        args.token = input("  Token: ").strip()
        if not args.token:
            print("  No token entered. Exiting.")
            sys.exit(1)
    if not args.tenant:
        args.tenant = input("  Tenant ID (e.g., 711): ").strip()
        if not args.tenant:
            print("  No tenant entered. Exiting.")
            sys.exit(1)
    if not args.count:
        count_str = input("  Count (default 10): ").strip()
        args.count = int(count_str) if count_str else 10
    return args


def main():
    args = parse_args()
    args = prompt_missing_args(args)
    count = args.count

    print("=" * 70)
    print("  COMMODITY BASE RATE — BATCH CREATE (API)")
    print(f"  Screen: {SCREEN_NAME}")
    print(f"  Entries to create: {count}")
    if args.dry_run:
        print("  ** DRY-RUN MODE — no entries will be created **")
    print("=" * 70)
    print()
    print("  NOTE: The ERP overrides to_date to 2099-12-30 (BUG-004).")
    print("  Strategy: find/create FREE locations, then CBR entries for them.")
    print("=" * 70)

    api = ErpApiClient()
    api.set_session_from_token(args.token, tenant_id=args.tenant)

    # ── Resolve FK IDs ────────────────────────────────────────────────
    print()
    print("  Resolving FK IDs from live ERP...")
    resolver = FkResolver(api)
    fk_ids = resolve_all_fk_ids(resolver)

    # ── Step 1: Fetch ALL locations ────────────────────────────────────
    print()
    print("  Step 1: Fetching all locations from ERP...")
    print("-" * 70)

    all_locations = fetch_all_location_ids(api)
    # Supplement with FkResolver results if they have extras
    loc_fk = fk_ids.get("location_ref_id", {})
    for name, lid in loc_fk.items():
        if name not in all_locations:
            all_locations[name] = lid

    print(f"  Total locations in ERP: {len(all_locations)}")
    print(f"  Static LOCATION_ID_MAP: {len(LOCATION_ID_MAP)} entries")
    print(f"  FkResolver: {len(loc_fk)} entries")
    print(f"  Dynamic (from dropdown): {len(all_locations) - len(LOCATION_ID_MAP)} additional")

    # ── Step 2: Find which locations already have CBR entries ──────────
    print()
    print("  Step 2: Checking existing CBR entries (with full dedup)...")
    print("-" * 70)

    used_locations = fetch_existing_cbr_locations(api, all_locations=all_locations)

    free_locations = {
        name: loc_id for name, loc_id in all_locations.items()
        if loc_id not in used_locations
    }

    print(f"  Locations with existing CBR: {len(used_locations)}")
    print(f"  FREE locations (no CBR): {len(free_locations)}")
    if free_locations:
        for name, lid in sorted(free_locations.items(), key=lambda x: x[1]):
            print(f"    - {name} (id={lid})")
    else:
        print("  (!) ALL locations already have CBR entries — must create new ones")

    # ── Step 3: Ensure enough free locations ──────────────────────────
    needed = count
    available = len(free_locations)
    will_create_locations = 0

    if available < needed:
        will_create_locations = needed - available
        print()
        if args.dry_run:
            print(f"  Step 3: Would need {needed} free locations, only {available} available.")
            print(f"  Would create {will_create_locations} new locations via Location API.")
            print()
        else:
            print(f"  Step 3: Need {needed} free locations, only {available} available.")
            print(f"  Creating {will_create_locations} new locations via the Location API...")
            print("-" * 70)

            existing_names = set(n.lower() for n in all_locations.keys())
            name_idx = 0
            created_locs = 0

            while created_locs < will_create_locations:
                candidate = None
                while name_idx < len(NEW_LOCATION_NAMES):
                    candidate = NEW_LOCATION_NAMES[name_idx]
                    name_idx += 1
                    if candidate.lower() not in existing_names:
                        break
                else:
                    fallback_num = name_idx + 1
                    candidate = f"CBR Test Location {fallback_num}"

                new_id = create_new_location(api, candidate)
                if new_id:
                    free_locations[candidate] = new_id
                    all_locations[candidate] = new_id
                    existing_names.add(candidate.lower())
                    created_locs += 1
                    print(f"    Created: {candidate} (id={new_id})")
                else:
                    print(f"    FAILED to create: {candidate}")
                    if name_idx >= len(NEW_LOCATION_NAMES) + 20:
                        print("  ERROR: Too many location creation failures — stopping")
                        break

                time.sleep(0.3)

            print(f"  Created {created_locs} new locations. Now have {len(free_locations)} free locations")
    else:
        print()
        print(f"  Step 3: {available} free locations available — enough for {needed}.")
        print("  No new locations needed.")

    # Build item map and UOM list from live FkResolver results
    item_map = fk_ids.get("item_ref_id", ITEM_ID_MAP)
    uom_list = list(fk_ids.get("uom", UOM_ID_MAP).values()) if fk_ids.get("uom") else list(UOM_ID_MAP.values())
    pricing_type_map = fk_ids.get("pricing_type_ref_id", {118: "Common", 120: "Supplier"})
    pricing_type_ids = list(pricing_type_map.keys()) if pricing_type_map else [118, 120]

    sorted_free = sorted(free_locations.items(), key=lambda x: x[1])

    # ── Dry-run: show what would be created ────────────────────────────
    if args.dry_run:
        print()
        print(f"  [DRY-RUN] Would create {count} CBR entries:")
        print(f"  Items per entry: {len(item_map)} ({', '.join(list(item_map.keys())[:3])}{'...' if len(item_map) > 3 else ''})")
        print("-" * 70)
        for i in range(count):
            if i >= len(sorted_free):
                print(f"    [{i+1}/{count}] No more free locations — would stop")
                break
            loc_name, loc_id = sorted_free[i]
            pt_id = pricing_type_ids[i % len(pricing_type_ids)]
            pt_name = pricing_type_map.get(pt_id, str(pt_id))
            print(f"    [{i+1}/{count}] CBR: {pt_name}/{loc_name} (loc_id={loc_id}) "
                  f"— {len(item_map)} detail rows, random rates 500-5000")
        if will_create_locations > 0:
            print(f"    (would also create {will_create_locations} new locations)")
        print()
        print("  [DRY-RUN] No entries were created.")
        api.close()
        return

    # ── Step 4: Create CBR entries ─────────────────────────────────────
    print()
    print(f"  Step 4: Creating {count} CBR entries ({len(item_map)} items each)...")
    print("-" * 70)

    results = []
    created = 0
    failed = 0

    for i in range(count):
        if i >= len(sorted_free):
            print(f"    [{i+1}/{count}] No more free locations — stopping")
            break

        loc_name, loc_id = sorted_free[i]
        pt_id = pricing_type_ids[i % len(pricing_type_ids)]
        pt_name = pricing_type_map.get(pt_id, str(pt_id))

        print(
            f"    [{i+1}/{count}] Creating CBR: {pt_name}/{loc_name} "
            f"(loc_id={loc_id}) {len(item_map)} items...",
            end=" ",
            flush=True,
        )

        result = create_cbr_entry(api, pt_id, loc_id,
                                   item_map=item_map,
                                   uom_list=uom_list)

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
                children = p.get("children", [])
                detail = children[0].get("details", [{}])[0] if children else {}
                item_id = detail.get("item_ref_id", "?")
                print(f"  FAILED (pricing={pt_id}, location={loc_id}, "
                      f"item={item_id}): {r.get('error', 'Unknown')}")

    if created < count:
        print(f"  WARNING: Only {created}/{count} entries created.")

    print(f"  Total: {created} created, {failed} failed")
    print("=" * 70)

    api.close()


if __name__ == "__main__":
    main()

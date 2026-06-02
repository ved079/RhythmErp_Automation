#!/usr/bin/env python3
"""
Commodity Base Rate — Batch Create via API

Creates CBR entries via the ERP API (bypasses the UI entirely).
Handles FK dropdown fields (Pricing Type, Location) and the
unique (to_date, location_ref_id) constraint.

IMPORTANT — Unique Constraint:
  The ERP enforces uniqueness on (to_date, location_ref_id). Each location
  can only have ONE CBR entry per to_date value. The script uses TWO dedup
  strategies:

  1. DYNAMIC FETCH: After authenticating, fetches all existing CBR entries
     from the API to discover which (to_date, location_ref_id) combos are
     already used, and passes these as skip_location_ids to the payload
     generator.

  2. RETRY ON DUPLICATE: If the API still rejects a payload with
     "Duplicate entry found for to_date, location_ref_id", the script
     shifts the to_date by 1 year and retries, or skips the entry.

NOTE — Grid Detail Rows:
  The ERP's API does NOT support creating grid detail rows (Item Name,
  Item Rate, UOM) via the main POST endpoint. The batch_create script
  creates HEADER-ONLY entries. Grid rows must be added through the UI
  or a separate mechanism.

Payload Structure (header-only):
  {
    "id": "",
    "attribute_name": "Commodity Base Rate",
    "pricing_type_ref_id": <int>,      // 118=Common, 120=Supplier
    "from_date": "<ISO datetime>",     // server auto-sets on create
    "to_date": "2099-12-30T18:30:00Z",
    "location_ref_id": <int>           // FK → Location table
  }

Usage:
    python batch_create.py              # Creates 10 entries
    python batch_create.py --count 20   # Creates 20 entries
    python batch_create.py --offset 5   # Skip first 5 in data pool

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
    generate_cbr_payloads,
    COMMODITY_BASE_RATE_API_DATA,
    PRICING_TYPE_ID_MAP,
    LOCATION_ID_MAP,
    CBR_USED_LOCATION_IDS,
)

SCREEN_NAME = "Commodity Base Rate"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Batch create Commodity Base Rate entries via API"
    )
    parser.add_argument(
        "--count", type=int, default=10,
        help="Number of entries to create. Default: 10"
    )
    parser.add_argument(
        "--offset", type=int, default=0,
        help="Start index in data pool (to skip already-used entries). Default: 0"
    )
    return parser.parse_args()


# ── Dynamic dedup: fetch used (to_date, location) combos from live ERP ──

def fetch_used_combos_from_api(api: ErpApiClient) -> set:
    """
    Fetch ALL existing CBR entries from the ERP listing API and extract
    (to_date_year, location_ref_id) pairs that are already in use.

    This is the COMPLETE dedup — the unique constraint is (to_date, location_ref_id),
    so we must track ALL combos across ALL years, not just the default to_date.
    The previous implementation only tracked locations with to_date=2099-12-30,
    which caused duplicate errors when trying to create entries with years
    that were already used (2098, 2097, etc.).

    Args:
        api: Authenticated ErpApiClient instance

    Returns:
        Set of (year, location_ref_id) tuples already used in CBR
    """
    used_combos = set()

    try:
        # Fetch listing with large page size to get all entries
        result = api.list_entries(SCREEN_NAME, page_size=200)
        if not result:
            log.warning(
                "[DEDUP] Could not fetch CBR listing — using static skip list only"
            )
            return used_combos

        entries = result.get("screenmatlistingdata_set", [])
        if not entries:
            log.info("[DEDUP] No existing CBR entries found in listing")
            return used_combos

        log.info(f"[DEDUP] Found {len(entries)} existing CBR entries in listing")

        unresolved = 0
        for entry in entries:
            loc_val = entry.get("location_ref_id")
            to_date = entry.get("to_date", "")

            # Parse year from to_date — handle multiple formats:
            #   ISO: "2099-12-30T18:30:00Z"  or  "2099-12-30"
            #   D/M/Y: "30/12/2099"
            year = None
            to_str = str(to_date)
            year_match = re.match(r'(\d{4})', to_str)
            if year_match:
                year = int(year_match.group(1))
            else:
                # Try DD/MM/YYYY format
                dm_match = re.search(r'(\d{2})/(\d{2})/(\d{4})', to_str)
                if dm_match:
                    year = int(dm_match.group(3))

            if year is None:
                continue

            # Resolve location_ref_id to integer
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
                used_combos.add((year, loc_id))
            else:
                unresolved += 1

        if unresolved:
            log.warning(
                f"[DEDUP] Could not resolve location_ref_id for "
                f"{unresolved} entries"
            )

        log.info(
            f"[DEDUP] Discovered {len(used_combos)} unique (year, location) "
            f"combos from API"
        )

        # Show summary by year — helps debug dedup issues
        years = sorted(set(y for y, _ in used_combos), reverse=True)
        for y in years:
            locs = sorted(l for yy, l in used_combos if yy == y)
            log.info(f"[DEDUP]   Year {y}: {len(locs)} locations used — {locs}")

    except Exception as e:
        log.warning(f"[DEDUP] Error fetching used combos from API: {e}")

    return used_combos


def create_with_retry(api: ErpApiClient, payloads: list, target_count: int,
                      delay: float = 0.3) -> list:
    """
    Create CBR entries one by one, skipping duplicates and retrying
    with shifted to_date.

    If the API rejects a payload with "Duplicate entry found for
    to_date, location_ref_id", the script shifts the to_date by
    -1 year and retries up to MAX_RETRIES times. If all retries fail,
    the entry is skipped.

    Args:
        api: Authenticated ErpApiClient
        payloads: List of payloads to try
        target_count: Number of successful creations desired
        delay: Seconds between API calls

    Returns:
        List of result dicts with success/error/payload info
    """
    MAX_RETRIES = 5  # Try up to 5 year shifts (e.g., 2099→2098→2097→2096→2095)
    results = []
    created = 0
    failed = 0
    skipped_dup = 0
    idx = 0

    while created < target_count and idx < len(payloads):
        payload = payloads[idx]
        idx += 1

        loc_id = payload.get("location_ref_id", "?")
        pt_id = payload.get("pricing_type_ref_id", "?")
        to_date = payload.get("to_date", "?")
        entry_name = f"entry-{idx} (pricing={pt_id}, location={loc_id}, to_date={to_date[:10]})"

        print(
            f"    [{created + 1}/{target_count}] Trying {entry_name}...",
            end=" ",
            flush=True,
        )

        result = api.create_entry(payload)

        if result is not None:
            results.append({"success": True, "data": result, "payload": payload})
            created += 1
            print("OK")
        else:
            # Duplicate detected — try multiple year shifts
            current_year = int(payload.get("to_date", "2099")[:4])
            retry_success = False

            for shift in range(1, MAX_RETRIES + 1):
                new_year = current_year - shift
                if new_year < 2026:
                    break
                new_to_date = payload["to_date"].replace(
                    str(current_year), str(new_year)
                )
                payload["to_date"] = new_to_date
                print(f"RETRY(y→{new_year})...", end=" ", flush=True)
                result2 = api.create_entry(payload)
                if result2 is not None:
                    results.append({
                        "success": True, "data": result2, "payload": payload
                    })
                    created += 1
                    print("OK")
                    retry_success = True
                    break

            if not retry_success:
                failed += 1
                skipped_dup += 1
                print("DUPLICATE — skipped")

                results.append({
                    "success": False,
                    "error": "Duplicate entry — skipped after retries",
                    "payload": payload,
                })

        if delay and idx < len(payloads):
            time.sleep(delay)

    log.info(
        f"[RETRY] Tried {idx} payloads, created {created}, "
        f"skipped {skipped_dup} duplicates, failed {failed - skipped_dup} other"
    )

    return results


def main():
    args = parse_args()
    count = args.count
    offset = args.offset

    print("=" * 70)
    print(f"  COMMODITY BASE RATE — BATCH CREATE (API)")
    print(f"  Screen: {SCREEN_NAME}")
    print(f"  Entries to create: {count}")
    print(f"  Data pool offset: {offset}")
    print(f"  Data pool size: {len(COMMODITY_BASE_RATE_API_DATA)}")
    print(f"  Pricing Type IDs: {len(PRICING_TYPE_ID_MAP)}")
    print(f"  Location IDs: {len(LOCATION_ID_MAP)}")
    print(f"  Static used location IDs (skip): {len(CBR_USED_LOCATION_IDS)}")
    print("=" * 70)

    api = ErpApiClient()
    token = api.prompt_for_token()
    api.set_session_from_token(token)

    # ── Dynamic dedup: fetch used (year, location) combos from live ERP ──
    print()
    print("  Fetching existing CBR entries from API for dynamic dedup...")
    dynamic_used_combos = fetch_used_combos_from_api(api)

    # ── Generate payloads (with dedup skip) ──────────────────────────
    # Generate MORE payloads than needed so retry logic has spares
    oversample = min(count * 2, len(COMMODITY_BASE_RATE_API_DATA))
    print()
    print(f"  Generating {oversample} candidate payloads (need {count} successful)...")
    print("-" * 70)

    try:
        payloads = generate_cbr_payloads(
            count=oversample,
            offset=offset,
            used_combos=dynamic_used_combos,
        )
    except Exception as e:
        print(f"  ERROR generating payloads: {e}")
        api.close()
        return

    if not payloads:
        print("  ERROR: No payloads generated. Data pool may be exhausted.")
        print("  → Add more (pricing_type, location) combos to "
              "COMMODITY_BASE_RATE_API_DATA, or")
        print("    use a different --offset value.")
        api.close()
        return

    print(f"  Generated {len(payloads)} candidate payloads")

    # Validate FK fields before sending
    for i, p in enumerate(payloads):
        missing = []
        if p.get("pricing_type_ref_id") is None:
            missing.append("pricing_type_ref_id")
        if p.get("location_ref_id") is None:
            missing.append("location_ref_id")
        if missing:
            print(f"  WARNING: Payload {i+1} has None FK fields: {missing}")

    # ── Create entries with retry ─────────────────────────────────────
    print()
    print(f"  Creating {count} entries on '{SCREEN_NAME}' "
          f"(with duplicate retry)...")
    print("-" * 70)

    results = create_with_retry(api, payloads, target_count=count)

    # ── Summary ───────────────────────────────────────────────────────
    created = sum(1 for r in results if r.get("success"))
    failed = sum(1 for r in results if not r.get("success"))
    skipped_dup = sum(
        1 for r in results
        if not r.get("success") and "Duplicate" in str(r.get("error", ""))
    )
    other_failed = failed - skipped_dup

    print()
    print("=" * 70)
    print("  FINAL SUMMARY")
    print("=" * 70)
    status_icon = "OK" if failed == 0 else "!!"
    print(f"  [{status_icon}] {SCREEN_NAME:<35} {created:>3}/{count} created")
    print("-" * 70)

    if other_failed > 0:
        for i, r in enumerate(results):
            if not r.get("success") and "Duplicate" not in str(r.get("error", "")):
                p = r.get("payload", {})
                loc_id = p.get("location_ref_id", "?")
                pt_id = p.get("pricing_type_ref_id", "?")
                print(f"  FAILED entry (pricing={pt_id}, location={loc_id}): "
                      f"{r.get('error', 'Unknown')}")

    if skipped_dup:
        print(f"  Skipped {skipped_dup} duplicates (these are expected — "
              f"combos already exist)")

    if created < count:
        print(f"  WARNING: Only {created}/{count} entries created. "
              f"Data pool may be exhausted.")
        print(f"  → Add more (pricing_type, location) combos to "
              f"COMMODITY_BASE_RATE_API_DATA, or")
        print(f"    try running with --offset to skip already-used entries.")

    print(f"  Total: {created} created, {skipped_dup} duplicates skipped, "
          f"{other_failed} other failures")
    print("=" * 70)

    api.close()


if __name__ == "__main__":
    main()

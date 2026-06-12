#!/usr/bin/env python3
"""
Commodity Quality Parameter — Batch Create via API

Creates CQP entries via the ERP API (bypasses the UI entirely).
Handles FK dropdown fields (Item Name, Transaction Type, Quality Parameter)
and properly creates detail rows inside the stepper grid.

IMPORTANT — Unique Constraint:
  The ERP enforces uniqueness on (item_ref_id, to_date). Each item can only
  have ONE CQP entry per to_date value. The script uses TWO dedup strategies:

  1. DYNAMIC FETCH: After authenticating, fetches all existing CQP entries
     from the API to discover which item_ref_ids are already used, and passes
     these as skip_item_ids to the payload generator.

  2. RETRY ON DUPLICATE: If the API still rejects a payload with "Duplicate
     entry found for item_ref_id, to_date", the script skips that entry and
     tries the next one from the pool, until count entries are created or
     the pool is exhausted.

Payload Structure (stepper with grid detail):
  {
    "id": "",
    "attribute_name": "Commodity Quality Parameter",
    "item_ref_id": <int>,          // FK → Item Master
    "transaction_type": <int>,     // FK → Transaction Type options
    "from_date": "<ISO datetime>", // Auto-set by server on create
    "to_date": "2099-12-30T18:30:00Z",
    "revision_status": "<str or null>",
    "details": [],
    "children": [
      {
        "stepper_name": "Define Item Quality Parameter Details",
        "is_stepper": true,
        "details": [                  <--- Quality param detail rows go here
          {
            "quality_type": <int>,    // FK → Quality Parameter
            "min_quality_value": "<str>",
            "max_quality_value": "<str>",
            "rate_percentage": <bool>,
            "multiplier": "<str>"
          }
        ],
        "children": []
      }
    ]
  }

Usage:
    python batch_create.py              # Creates 10 entries
    python batch_create.py --count 20   # Creates 20 entries
    python batch_create.py --offset 10  # Skip first 10 in data pool

Screen: Commodity Quality Parameter
URL:    /#/dynamic-screens/Commodity%20Quality%20Parameter
"""

import sys
import os
import argparse
import time

# ── Path setup ────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from common.erp_api_client import ErpApiClient
from common.fk_resolver import FkResolver
from common.logger import log
from pages.commodity_settings.modules.commodity_quality_parameter.data.commodity_quality_parameter_data import (
    generate_cqp_payloads,
    COMMODITY_QUALITY_PARAMETER_API_DATA,
    TRANSACTION_TYPE_ID_MAP,
)

SCREEN_NAME = "Commodity Quality Parameter"

# FK fields that need resolution from live ERP
FK_SCREEN_MAP = {
    "item_ref_id": "Item Master",
    "quality_type": "Quality Parameter Master",
}


def parse_args():
    parser = argparse.ArgumentParser(description="Batch create Commodity Quality Parameter entries via API")
    parser.add_argument(
        "--count", type=int, default=None,
        help="Number of entries to create (omit to prompt)"
    )
    parser.add_argument(
        "--offset", type=int, default=0,
        help="Start index in data pool (to skip already-used entries). Default: 0"
    )
    parser.add_argument("--token", default=None, help="ERP Bearer token (omit to prompt)")
    parser.add_argument("--tenant", default=None, help="Tenant ID (omit to prompt)")
    parser.add_argument("--dry-run", action="store_true", help="Print payloads without sending")
    return parser.parse_args()


# ── Dynamic dedup: fetch used item IDs from the live ERP ──────────────

def fetch_used_item_ids_from_api(api: ErpApiClient) -> set:
    """
    Fetch existing CQP entries from the ERP listing API and extract
    item_ref_id values that are already used (with the default to_date).

    This provides RUNTIME dedup — even if the static CQP_USED_ITEM_IDS
    is stale, the dynamic fetch ensures we don't create duplicates.

    Args:
        api: Authenticated ErpApiClient instance

    Returns:
        Set of item_ref_id integers already used in CQP
    """
    used_ids = set()

    try:
        # Fetch listing with large page size to get all entries
        result = api.list_entries(SCREEN_NAME, page_size=200)
        if not result:
            log.warning("[DEDUP] Could not fetch CQP listing — using static skip list only")
            return used_ids

        entries = result.get("screenmatlistingdata_set", [])
        if not entries:
            log.info("[DEDUP] No existing CQP entries found in listing")
            return used_ids

        log.info(f"[DEDUP] Found {len(entries)} existing CQP entries in listing")

        # Strategy 1: Look for item_ref_id directly in listing data
        for entry in entries:
            # Try direct field name
            item_id = entry.get("item_ref_id")
            if item_id is not None:
                try:
                    used_ids.add(int(item_id))
                    continue
                except (ValueError, TypeError):
                    pass

            # Try common alternate field names
            for key in ("item_ref_id_name", "item_name", "item"):
                val = entry.get(key)
                if val and isinstance(val, str):
                    # Reverse-lookup: find the ID from ITEM_ID_MAP
                    for name, id_val in ITEM_ID_MAP.items():
                        if name.lower() == val.lower():
                            used_ids.add(id_val)
                            break

        # Strategy 2: If no IDs found from listing, fetch detailed entries
        # This is slower but more reliable — fetches each entry's detail
        if not used_ids and entries:
            log.info("[DEDUP] Listing has no item_ref_id; fetching detail entries...")
            for i, entry in enumerate(entries[:50]):  # Cap at 50 to avoid too many calls
                entry_id = entry.get("id")
                if entry_id is None:
                    continue
                detail = api.get_entry(SCREEN_NAME, entry_id)
                if detail and "item_ref_id" in detail:
                    try:
                        used_ids.add(int(detail["item_ref_id"]))
                    except (ValueError, TypeError):
                        pass
                if i > 0 and i % 10 == 0:
                    time.sleep(0.2)  # Small delay to avoid rate limiting

        log.info(f"[DEDUP] Discovered {len(used_ids)} used item_ref_ids from API: {sorted(used_ids)}")

    except Exception as e:
        log.warning(f"[DEDUP] Error fetching used items from API: {e}")

    return used_ids


def create_with_retry(api: ErpApiClient, payloads: list, target_count: int,
                      delay: float = 0.3) -> list:
    """
    Create CQP entries one by one, skipping duplicates and retrying
    with the next payload until target_count entries are created.

    If the API rejects a payload with "Duplicate entry found for
    item_ref_id, to_date", the item_ref_id is added to the skip set
    and the next payload is tried.

    Args:
        api: Authenticated ErpApiClient
        payloads: List of payloads to try (should be more than target_count)
        target_count: Number of successful creations desired
        delay: Seconds between API calls

    Returns:
        List of result dicts: [{"success": bool, "data": ..., "error": ..., "payload": ...}, ...]
    """
    results = []
    created = 0
    failed = 0
    skipped_dup = 0
    idx = 0

    while created < target_count and idx < len(payloads):
        payload = payloads[idx]
        idx += 1

        item_id = payload.get("item_ref_id", "?")
        entry_name = f"entry-{idx} (item_ref_id={item_id})"

        print(f"    [{created + 1}/{target_count}] Trying {entry_name}...", end=" ", flush=True)

        result = api.create_entry(payload)

        if result is not None:
            results.append({"success": True, "data": result, "payload": payload})
            created += 1
            print("OK")
        else:
            # Check if this was a duplicate error — if so, just skip it
            # (The error was already logged by create_entry)
            failed += 1
            skipped_dup += 1
            print("DUPLICATE — skipped")

            results.append({
                "success": False,
                "error": "Duplicate entry — skipped",
                "payload": payload,
            })

        if delay and idx < len(payloads):
            time.sleep(delay)

    # Report how many we tried vs how many we needed
    log.info(
        f"[RETRY] Tried {idx} payloads, created {created}, "
        f"skipped {skipped_dup} duplicates, failed {failed - skipped_dup} other"
    )

    return results


def resolve_all_fk_ids(resolver):
    """Resolve all CQP FK IDs from the live ERP."""
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
    offset = args.offset

    print("=" * 70)
    print(f"  COMMODITY QUALITY PARAMETER — BATCH CREATE (API)")
    print(f"  Screen: {SCREEN_NAME}")
    print(f"  Entries to create: {count}")
    print(f"  Data pool offset: {offset}")
    print(f"  Data pool size: {len(COMMODITY_QUALITY_PARAMETER_API_DATA)}")
    if args.dry_run:
        print("  ** DRY-RUN MODE — no entries will be created **")
    print("=" * 70)

    api = ErpApiClient()
    api.set_session_from_token(args.token, tenant_id=args.tenant)

    # ── Resolve FK IDs ────────────────────────────────────────────────
    print()
    print("  Resolving FK IDs from live ERP...")
    resolver = FkResolver(api)
    fk_ids = resolve_all_fk_ids(resolver)

    # ── Dynamic dedup: fetch used item IDs from live ERP ──────────────
    print()
    print("  Fetching existing CQP entries from API for dynamic dedup...")
    dynamic_used_ids = fetch_used_item_ids_from_api(api)

    # ── Generate payloads (with dedup skip) ──────────────────────────
    # Generate MORE payloads than needed so retry logic has spares
    oversample = min(count * 3, len(COMMODITY_QUALITY_PARAMETER_API_DATA))
    print()
    print(f"  Generating {oversample} candidate payloads (need {count} successful)...")
    print("-" * 70)

    try:
        payloads = generate_cqp_payloads(
            count=oversample,
            offset=offset,
            skip_item_ids=dynamic_used_ids,
            fk_ids=fk_ids,
        )
    except Exception as e:
        print(f"  ERROR generating payloads: {e}")
        api.close()
        return

    if not payloads:
        print("  ERROR: No payloads generated. Data pool may be exhausted.")
        print("  >> Add more items to COMMODITY_QUALITY_PARAMETER_API_DATA or")
        print("    use a different --offset value.")
        api.close()
        return

    print(f"  Generated {len(payloads)} candidate payloads")

    if args.dry_run:
        print(f"  [DRY-RUN] {len(payloads)} payloads generated")
        for j, p in enumerate(payloads):
            item_id = p.get("item_ref_id", "?")
            txn_type = p.get("transaction_type", "?")
            stepper = p.get("children", [{}])[0] if p.get("children") else {}
            detail_count = len(stepper.get("details", []))
            print(f"    [{j+1}] item_ref_id={item_id} txn_type={txn_type} details={detail_count}")
        api.close()
        return

    # Validate FK fields before sending
    for i, p in enumerate(payloads):
        missing = []
        if p.get("item_ref_id") is None:
            missing.append("item_ref_id")
        if p.get("transaction_type") is None:
            missing.append("transaction_type")
        stepper = p.get("children", [{}])[0] if p.get("children") else {}
        detail_rows = stepper.get("details", [])
        for j, row in enumerate(detail_rows):
            if row.get("quality_type") is None:
                missing.append(f"detail[{j}].quality_type")
        if missing:
            print(f"  WARNING: Payload {i+1} has None FK fields: {missing}")

    # ── Create entries with retry ─────────────────────────────────────
    print()
    print(f"  Creating {count} entries on '{SCREEN_NAME}' (with duplicate retry)...")
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
                item_id = p.get("item_ref_id", "?")
                print(f"  FAILED entry (item_ref_id={item_id}): {r.get('error', 'Unknown')}")

    if skipped_dup:
        print(f"  Skipped {skipped_dup} duplicates (these are expected — items already exist)")

    if created < count:
        print(f"  WARNING: Only {created}/{count} entries created. "
              f"Data pool may be exhausted.")
        print(f"  >> Add more items to COMMODITY_QUALITY_PARAMETER_API_DATA, or")
        print(f"    try running with --offset to skip already-used entries.")

    print(f"  Total: {created} created, {skipped_dup} duplicates skipped, "
          f"{other_failed} other failures")
    print("=" * 70)

    api.close()


if __name__ == "__main__":
    main()

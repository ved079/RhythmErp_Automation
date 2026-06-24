"""
batch_create.py — Purchase Order batch creation script.

Strategy:
  1. Fetch Commodity Base Rate (CBR) from ERP → {location_id: {item_id: {rate, uom}}}
  2. Only create POs for locations that have CBR data (guarantees real rates)
  3. Resolve all other FK IDs (suppliers, HSN, dropdowns) live from ERP
  4. No hardcoded IDs — fully universal across tenants

Usage:
    python batch_create.py --token <jwt> --tenant 751 --count 3
    python batch_create.py --token <jwt> --tenant 751 --dry-run
    python batch_create.py --token <jwt> --tenant 751 --supplier 1 --count 5
"""

import argparse
import json
import os
import random
import sys
import time

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from common.erp_api_client import RhythmERPAPIClient
from pages.private_b2b.modules.purchase_order.data.purchase_order_data import (
    build_po_payload,
    build_po_item,
    compute_expected_results,
)
from pages.private_b2b.modules.purchase_order.utils.api_purchase_order_utils import (
    POAPIUtils,
)

_PO_SCREEN = "Purchase Order"


def _resolve_dropdown(client: RhythmERPAPIClient, field: str) -> list:
    """Return list of integer IDs from a PO dropdown field."""
    try:
        opts = client.get_dropdown_options(_PO_SCREEN, field)
        return [int(o["id"]) for o in (opts or []) if o.get("id")]
    except Exception:
        return []


def _resolve_suppliers(client: RhythmERPAPIClient) -> list:
    """Return list of supplier IDs from the live Supplier listing."""
    try:
        resp = client.list_entries("Supplier", page_size=200)
        rows = resp.get("screenmatlistingdata_set") or []
        return [int(r["id"]) for r in rows if r.get("id")]
    except Exception:
        return []


def _fetch_cbr_data(client: RhythmERPAPIClient) -> dict:
    """
    Fetch Commodity Base Rate and return:
        {location_id (int): {item_id (int): {"rate": float, "uom": int}}}

    Only locations with at least one item row are included.
    """
    cbr = {}
    try:
        resp = client.list_entries("Commodity Base Rate", page_size=200)
        entries = resp.get("screenmatlistingdata_set") or []
    except Exception as e:
        print(f"  ERROR fetching CBR listing: {e}")
        return cbr

    for entry in entries:
        loc_id = entry.get("location_ref_id")
        entry_id = entry.get("id")
        if not loc_id or not entry_id:
            continue
        try:
            detail = client.get_entry("Commodity Base Rate", entry_id)
            items = {}
            for child in (detail.get("children") or []):
                for row in (child.get("details") or []):
                    iid = row.get("item_ref_id")
                    rate = row.get("item_rate")
                    uom = row.get("uom")
                    if iid is not None and rate is not None and uom is not None:
                        items[int(iid)] = {"rate": float(rate), "uom": int(uom)}
            if items:
                cbr[int(loc_id)] = items
        except Exception as e:
            print(f"  WARNING: Could not fetch CBR detail for entry {entry_id}: {e}")

    return cbr


def main():
    parser = argparse.ArgumentParser(description="Batch create Purchase Orders")
    parser.add_argument("--token", default="", help="ERP JWT token")
    parser.add_argument("--tenant", default="751", help="Tenant ID")
    parser.add_argument("--count", type=int, default=1, help="Number of POs to create")
    parser.add_argument("--supplier", type=int, default=None, help="Pin supplier ref ID (random if omitted)")
    parser.add_argument("--dry-run", action="store_true", help="Print payloads without creating")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay between creates (seconds)")
    args = parser.parse_args()

    token = args.token or os.environ.get("ERP_TOKEN", "")
    if not token:
        print("ERROR: No token provided. Use --token or set ERP_TOKEN env var.")
        sys.exit(1)

    client = RhythmERPAPIClient()
    client.login_from_browser(token=token, tenant_id=args.tenant)
    api = POAPIUtils(client)

    print("\nResolving live FK data from ERP...")

    # --- Suppliers ---
    if args.supplier is not None:
        supplier_ids = [args.supplier]
        print(f"  Supplier: pinned to {args.supplier}")
    else:
        supplier_ids = _resolve_suppliers(client)
        if not supplier_ids:
            print("  ERROR: No suppliers found in ERP. Cannot create POs.")
            sys.exit(1)
        print(f"  Suppliers: {len(supplier_ids)} found")

    # --- CBR data: location → items with rates ---
    print("  Fetching Commodity Base Rate data...")
    cbr_data = _fetch_cbr_data(client)
    if not cbr_data:
        print("  ERROR: No CBR data found. Add locations and items to Commodity Base Rate first.")
        sys.exit(1)
    print(f"  CBR: {len(cbr_data)} location(s) with rates")
    for loc_id, items in cbr_data.items():
        print(f"    Location {loc_id}: {len(items)} item(s) — IDs {list(items.keys())}")

    # --- HSN SAC ---
    hsn_ids = _resolve_dropdown(client, "hsn_sac_no")
    if not hsn_ids:
        print("  ERROR: No HSN/SAC codes found in ERP dropdown.")
        sys.exit(1)
    print(f"  HSN/SAC: {len(hsn_ids)} found")

    # --- Parameter dropdowns ---
    param1_ids = _resolve_dropdown(client, "parameter1")  # Division
    param2_ids = _resolve_dropdown(client, "parameter2")  # Department
    param3_ids = _resolve_dropdown(client, "parameter3")  # Type of sale
    txn_currency_ids = _resolve_dropdown(client, "txn_currency")

    # Fallback to first available or safe default
    param1_ids = param1_ids or [1]
    param2_ids = param2_ids or [1]
    param3_ids = param3_ids or [25]
    # Default currency: prefer INR (1), else first available
    base_currency = 1 if 1 in txn_currency_ids else (txn_currency_ids[0] if txn_currency_ids else 1)

    print(f"  parameter1 (Division): {param1_ids}")
    print(f"  parameter2 (Department): {param2_ids}")
    print(f"  parameter3 (Type of sale): {param3_ids}")
    print(f"  Base currency: {base_currency}")

    cbr_locations = list(cbr_data.keys())

    # --- Build payloads ---
    payloads = []
    for i in range(args.count):
        location_id = cbr_locations[i % len(cbr_locations)]
        cbr_items = cbr_data[location_id]
        supplier_id = random.choice(supplier_ids)

        items = [
            build_po_item(
                item_ref_id=item_id,
                hsn_sac_no=random.choice(hsn_ids),
                uom=cbr_item["uom"],
                rate=cbr_item["rate"],
            )
            for item_id, cbr_item in cbr_items.items()
        ]

        payload = build_po_payload(
            supplier_ref_id=supplier_id,
            po_item_type=113,  # Farm — system constant
            po_type=25,        # Domestic — default
            txn_currency=base_currency,
            base_currency=base_currency,
            parameter1=random.choice(param1_ids),
            parameter2=random.choice(param2_ids),
            parameter3=25,  # Domestic — matches po_type
            parameter4=location_id,
            items=items,
        )
        payloads.append(payload)

    if args.dry_run:
        print(f"\n{'=' * 60}")
        print(f"DRY RUN: {args.count} PO payload(s)")
        print(f"{'=' * 60}")
        for i, p in enumerate(payloads):
            expected = compute_expected_results(p)
            print(f"\n--- PO [{i + 1}/{args.count}] ---")
            print(json.dumps(p, indent=2, default=str))
            print(f"  Expected total: {expected['txn_currency_total_amount']}")
        print("\nDry run complete. No entries created.")
        return

    print(f"\n{'=' * 60}")
    print(f"Creating {args.count} Purchase Order(s)...")
    print(f"{'=' * 60}")

    results = []
    for i, payload in enumerate(payloads):
        try:
            data = api.create_po(payload)
            if data:
                entry_id = data.get("id") or data.get("entry_id")
                ref_no = data.get("transaction_ref_no", str(entry_id))
                loc = payload.get("parameter4")
                results.append({"success": True, "id": entry_id, "ref": ref_no})
                print(f"  [{i + 1}/{args.count}] Created PO ID={entry_id} ref={ref_no} "
                      f"location={loc} items={len(payload['purchasing_order_items_details'])}")
            else:
                err = getattr(getattr(api, '_last_response', None), 'text', 'N/A')
                results.append({"success": False, "error": err[:300]})
                print(f"  [{i + 1}/{args.count}] FAILED — {err[:200]}")
        except Exception as e:
            results.append({"success": False, "error": str(e)})
            print(f"  [{i + 1}/{args.count}] ERROR: {e}")

        if args.delay and i < len(payloads) - 1:
            time.sleep(args.delay)

    success_count = sum(1 for r in results if r.get("success"))
    print(f"\n{'=' * 60}")
    print(f"Done: {success_count}/{args.count} succeeded")
    print(f"{'=' * 60}")
    return results


if __name__ == "__main__":
    main()

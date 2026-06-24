"""
batch_create.py — Purchase Booking batch creation script.

Strategy (strictly universal — zero hardcoded tenant IDs):
  1. Fetch Commodity Base Rate (CBR) -> {location_id: {item_id: {rate, uom}}}
     Rate and UOM for each item come from CBR, keyed by location.
  2. Fetch all Suppliers from live ERP listing.
  3. Resolve Division, Department, Type of Sale, Currency from PB dropdowns.
  4. Fetch QC entries per supplier (optional link).
  5. Create one PB per (supplier x location) combination using CBR rates.

Usage:
    python batch_create.py --token <jwt> --tenant 751 --count 3
    python batch_create.py --token <jwt> --tenant 751 --dry-run
    python batch_create.py --token <jwt> --tenant 751 --supplier 1 --count 5
    python batch_create.py --token <jwt> --tenant 751 --supplier-type farmer
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
from pages.private_b2b.modules.purchase_booking.data.purchase_booking_data import (
    SUPPLIER_TYPE_FARMER,
    SUPPLIER_TYPE_SUPPLIER,
    SUPPLIER_TYPE_NAMES,
    build_pb_item,
    build_pb_payload,
    compute_master_total,
)
from pages.private_b2b.modules.purchase_booking.utils.api_purchase_booking_utils import (
    PBAPIUtils,
)

_SCREEN = "Purchase Booking"

_SUPPLIER_TYPE_ALIASES = {
    "farmer":   SUPPLIER_TYPE_FARMER,
    "supplier": SUPPLIER_TYPE_SUPPLIER,
}


# ── FK resolution helpers ─────────────────────────────────────────────────────

def _resolve_dropdown(client: RhythmERPAPIClient, field: str) -> list:
    """Return list of integer IDs from a PB dropdown field."""
    try:
        opts = client.get_dropdown_options(_SCREEN, field)
        return [int(o["id"]) for o in (opts or []) if o.get("id") is not None]
    except Exception:
        return []


def _resolve_dropdown_with_names(client: RhythmERPAPIClient, field: str) -> dict:
    """Return {name: id} map from a PB dropdown field (key -> id)."""
    try:
        opts = client.get_dropdown_options(_SCREEN, field)
        return {str(o["key"]): int(o["id"]) for o in (opts or []) if o.get("id") and o.get("key")}
    except Exception:
        return {}


def _resolve_suppliers(client: RhythmERPAPIClient) -> list:
    """Return list of supplier IDs from the live Supplier listing."""
    try:
        resp = client.list_entries("Supplier", page_size=200)
        rows = resp.get("screenmatlistingdata_set") or []
        return [int(r["id"]) for r in rows if r.get("id")]
    except Exception:
        return []


def _fetch_cbr_data(client: RhythmERPAPIClient, location_name_to_id: dict) -> dict:
    """
    Fetch Commodity Base Rate and return:
        {location_id (int): {item_id (int): {"rate": float, "uom": int}}}

    The CBR listing returns location_ref_id as a display name (e.g. "Pune"),
    not an integer ID.  `location_name_to_id` maps name -> integer ID and is
    built from the PB parameter5 dropdown before calling this function.

    Only locations with at least one item row are included.
    """
    cbr: dict = {}
    try:
        resp = client.list_entries("Commodity Base Rate", page_size=200)
        entries = resp.get("screenmatlistingdata_set") or []
    except Exception as e:
        print(f"  ERROR fetching CBR listing: {e}")
        return cbr

    for entry in entries:
        loc_raw  = entry.get("location_ref_id")
        entry_id = entry.get("id")
        if not loc_raw or not entry_id:
            continue

        # Resolve location name -> integer ID
        if isinstance(loc_raw, int):
            loc_id = loc_raw
        elif isinstance(loc_raw, str) and loc_raw.isdigit():
            loc_id = int(loc_raw)
        else:
            loc_id = location_name_to_id.get(str(loc_raw))
            if loc_id is None:
                print(f"  WARNING: Cannot resolve location '{loc_raw}' -> skipping CBR entry {entry_id}")
                continue

        try:
            detail = client.get_entry("Commodity Base Rate", entry_id)
            items: dict = {}
            for child in (detail.get("children") or []):
                for row in (child.get("details") or []):
                    iid  = row.get("item_ref_id")
                    rate = row.get("item_rate")
                    uom  = row.get("uom")
                    if iid is not None and rate is not None and uom is not None:
                        items[int(iid)] = {"rate": float(rate), "uom": int(uom)}
            if items:
                cbr[int(loc_id)] = items
        except Exception as e:
            print(f"  WARNING: Could not fetch CBR detail for entry {entry_id}: {e}")

    return cbr


def _resolve_qc_for_supplier(client: RhythmERPAPIClient, supplier_id: int) -> list:
    """Return QC entry IDs for the given supplier. Returns [] if none found."""
    try:
        resp = client.list_entries("QC", page_size=50)
        if not resp:
            return []
        rows = resp.get("screenmatlistingdata_set") or []
        return [
            int(r["id"])
            for r in rows
            if r.get("id") and r.get("supplier_ref_id") == supplier_id
        ]
    except Exception:
        return []


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Batch create Purchase Bookings")
    parser.add_argument("--token",     default="",          help="ERP JWT token")
    parser.add_argument("--tenant",    default="751",       help="Tenant ID")
    parser.add_argument("--count",     type=int, default=1, help="Number of PBs to create")
    parser.add_argument("--supplier",  type=int, default=None, help="Pin supplier ref ID")
    parser.add_argument(
        "--supplier-type",
        default="farmer",
        choices=list(_SUPPLIER_TYPE_ALIASES.keys()),
        help="Supplier role type (farmer|supplier). Default: farmer",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print payloads, no creates")
    parser.add_argument("--delay",   type=float, default=0.5, help="Delay between creates (s)")
    args = parser.parse_args()

    token = args.token or os.environ.get("ERP_TOKEN", "")
    if not token:
        print("ERROR: No token provided. Use --token or set ERP_TOKEN env var.")
        sys.exit(1)

    client = RhythmERPAPIClient()
    client.login_from_browser(token=token, tenant_id=args.tenant)
    api = PBAPIUtils(client)

    desired_supplier_type_id = _SUPPLIER_TYPE_ALIASES[args.supplier_type]

    print("\nResolving live FK data from ERP...")

    # ── Suppliers ─────────────────────────────────────────────────────────────
    if args.supplier is not None:
        supplier_ids = [args.supplier]
        print(f"  Supplier: pinned to {args.supplier}")
    else:
        supplier_ids = _resolve_suppliers(client)
        if not supplier_ids:
            print("  ERROR: No suppliers found in ERP. Cannot create PBs.")
            sys.exit(1)
        print(f"  Suppliers: {len(supplier_ids)} found -> {supplier_ids[:5]}")

    # ── Location name -> ID map (needed to resolve CBR listing strings) ───────
    loc_name_to_id = _resolve_dropdown_with_names(client, "parameter5")
    print(f"  Locations resolved: {loc_name_to_id}")

    # ── CBR data ──────────────────────────────────────────────────────────────
    print("  Fetching Commodity Base Rate data...")
    cbr_data = _fetch_cbr_data(client, loc_name_to_id)
    if not cbr_data:
        print("  ERROR: No CBR data found. Add items to Commodity Base Rate first.")
        sys.exit(1)
    print(f"  CBR: {len(cbr_data)} location(s)")
    for loc_id, items in cbr_data.items():
        print(f"    Location {loc_id}: {len(items)} item(s) -> {list(items.keys())}")

    # ── HSN SAC ───────────────────────────────────────────────────────────────
    hsn_ids = _resolve_dropdown(client, "hsn_sac_no")
    if not hsn_ids:
        print("  ERROR: No HSN/SAC codes found. Cannot create PBs.")
        sys.exit(1)
    print(f"  HSN/SAC: {len(hsn_ids)} found")

    # ── Parameter dropdowns ───────────────────────────────────────────────────
    param1_ids   = _resolve_dropdown(client, "parameter1") or [1]  # Division
    param2_ids   = _resolve_dropdown(client, "parameter2") or [1]  # Department
    param6_ids   = _resolve_dropdown(client, "parameter6") or [1]  # Type of Sale
    currency_ids = _resolve_dropdown(client, "base_currency")
    inr_id = 8 if 8 in currency_ids else (currency_ids[0] if currency_ids else 8)

    print(f"  Division (param1):     {param1_ids}")
    print(f"  Department (param2):   {param2_ids}")
    print(f"  Type of Sale (param6): {param6_ids}")
    print(f"  Currency (INR):        {inr_id}")
    print(f"  Supplier type:         {desired_supplier_type_id} ({SUPPLIER_TYPE_NAMES.get(desired_supplier_type_id, '?')})")

    cbr_locations = list(cbr_data.keys())

    # ── Build payloads ────────────────────────────────────────────────────────
    payloads = []
    for i in range(args.count):
        location_id = cbr_locations[i % len(cbr_locations)]
        cbr_items   = cbr_data[location_id]
        supplier_id = random.choice(supplier_ids)

        qc_ids    = _resolve_qc_for_supplier(client, supplier_id)
        qc_ref_id = qc_ids[0] if qc_ids else None

        items = [
            build_pb_item(
                item_ref_id=item_id,
                hsn_sac_no=random.choice(hsn_ids),
                alternate_uom=cbr_item["uom"],   # CBR UOM is the alternate UOM
                uom=cbr_item["uom"],              # use same as alternate if base unknown
                rate=cbr_item["rate"],
                no_of_bags=random.randint(1, 50),
            )
            for item_id, cbr_item in cbr_items.items()
        ]

        payload = build_pb_payload(
            supplier_ref_id=supplier_id,
            supplier_ref_type=desired_supplier_type_id,
            parameter1=random.choice(param1_ids),
            parameter2=random.choice(param2_ids),
            parameter5=location_id,
            parameter6=random.choice(param6_ids),
            base_currency=inr_id,
            txn_currency=inr_id,
            items=items,
            qc_ref_id=qc_ref_id,
        )
        payloads.append(payload)

    # ── Dry run ───────────────────────────────────────────────────────────────
    if args.dry_run:
        sep = "=" * 60
        print(f"\n{sep}\nDRY RUN: {args.count} PB payload(s)\n{sep}")
        for i, p in enumerate(payloads):
            print(f"\n--- PB [{i+1}/{args.count}] ---")
            print(json.dumps(p, indent=2, default=str))
            print(f"  Expected total: {p['txn_currency_amount']}")
        print("\nDry run complete. No entries created.")
        return

    # ── Create ────────────────────────────────────────────────────────────────
    sep = "=" * 60
    print(f"\n{sep}\nCreating {args.count} Purchase Booking(s)...\n{sep}")

    results = []
    for i, payload in enumerate(payloads):
        try:
            data = api.create_pb(payload)
            if data:
                entry_id = data.get("id") or data.get("entry_id")
                ref_no   = data.get("transaction_ref_no", str(entry_id))
                loc      = payload.get("parameter5")
                n_items  = len(payload.get("purchase_booking_details", []))
                total    = payload["txn_currency_amount"]
                results.append({"success": True, "id": entry_id, "ref": ref_no})
                print(
                    f"  [{i+1}/{args.count}] Created PB ID={entry_id} "
                    f"ref={ref_no} location={loc} items={n_items} total={total}"
                )
            else:
                resp = api.last_response()
                err  = resp.text[:300] if resp else "No response"
                status = api._last_status
                results.append({"success": False, "error": err})
                print(f"  [{i+1}/{args.count}] FAILED (HTTP {status}) - {err[:200]}")
        except Exception as e:
            results.append({"success": False, "error": str(e)})
            print(f"  [{i+1}/{args.count}] ERROR: {e}")

        if args.delay and i < len(payloads) - 1:
            time.sleep(args.delay)

    ok = sum(1 for r in results if r.get("success"))
    print(f"\n{sep}\nDone: {ok}/{args.count} succeeded\n{sep}")
    return results


if __name__ == "__main__":
    main()

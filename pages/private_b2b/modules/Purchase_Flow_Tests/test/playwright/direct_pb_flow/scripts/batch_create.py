"""
batch_create.py — Direct PB batch creation script.

Tenant: Eco Green Pvt Ltd (kedar@rhythmflows.com)
Flow:   Standalone Purchase Booking — no PO / QC / GRN reference.

Strategy:
  1. Resolve all FK IDs live from ERP (suppliers, items, HSN, UOM, dropdowns).
  2. Fetch item details to get HSN SAC No, alternate UOM, and UOM conversion per item.
  3. Build one PB per run using data/direct_pb_data.py builders.
  4. POST and report results.

Usage:
    python batch_create.py --token <jwt> --count 3
    python batch_create.py --token <jwt> --count 1 --dry-run
    python batch_create.py --token <jwt> --count 5 --supplier 2
"""

import argparse
import json
import os
import random
import sys
import time

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from common.erp_api_client import RhythmERPAPIClient
from pages.private_b2b.modules.purchase_booking.utils.api_purchase_booking_utils import PBAPIUtils
from pages.private_b2b.modules.Purchase_Flow_Tests.test.playwright.direct_pb_flow.data.direct_pb_data import (
    build_direct_pb_item,
    build_direct_pb_payload,
    compute_master_total,
)

_SCREEN = "Purchase Booking"
DEFAULT_TENANT = "Eco Green Pvt Ltd"
DEFAULT_EMAIL = "kedar@rhythmflows.com"


# ── FK resolution helpers ─────────────────────────────────────────────────────

def _resolve_dropdown(client: RhythmERPAPIClient, field: str) -> list:
    try:
        opts = client.get_dropdown_options(_SCREEN, field)
        return [int(o["id"]) for o in (opts or []) if o.get("id") is not None]
    except Exception:
        return []


def _resolve_dropdown_with_names(client: RhythmERPAPIClient, field: str) -> dict:
    """Return {name: id} from a PB dropdown field."""
    try:
        opts = client.get_dropdown_options(_SCREEN, field)
        return {str(o["key"]): int(o["id"]) for o in (opts or []) if o.get("id") and o.get("key")}
    except Exception:
        return {}


def _resolve_suppliers(client: RhythmERPAPIClient) -> list:
    """Return list of {id, name} dicts from the live Supplier listing."""
    try:
        resp = client.list_entries("Supplier", page_size=200)
        rows = resp.get("screenmatlistingdata_set") or []
        return [{"id": int(r["id"]), "name": str(r.get("name", r["id"]))} for r in rows if r.get("id")]
    except Exception:
        return []


def _resolve_items(client: RhythmERPAPIClient) -> list:
    """
    Return list of active items with their IDs and names.
    Each entry: {id, name}
    """
    try:
        resp = client.list_entries("Item Master", page_size=200)
        rows = resp.get("screenmatlistingdata_set") or []
        return [{"id": int(r["id"]), "name": str(r.get("name", ""))} for r in rows if r.get("id")]
    except Exception:
        return []


def _resolve_item_detail(client: RhythmERPAPIClient, item_id: int) -> dict:
    """
    Fetch item detail to extract hsn_sac_no, alternate_uom, uom_conversion.
    Returns {} if the detail cannot be fetched.

    Real field names from Item Master GET response:
      hsn_sac_code       → maps to hsn_sac_no in PB payload
      base_uom           → alternate UOM for the PB line
      base_uom_conversion → uom_conversion for the PB line
    """
    try:
        detail = client.get_entry("Item Master", item_id)
        hsn = detail.get("hsn_sac_code")
        alternate_uom = detail.get("uom")        # primary UOM → alternate_uom in PB line
        uom = detail.get("base_uom")             # base/weight UOM → uom in PB line
        conv = float(detail.get("base_uom_conversion") or 1.0)
        return {
            "hsn_sac_no": hsn,
            "alternate_uom": alternate_uom,
            "uom": uom,
            "uom_conversion": conv,
        }
    except Exception:
        return {}


def _resolve_payment_terms(client: RhythmERPAPIClient) -> list:
    """Return list of payment terms IDs from the PB dropdown."""
    return _resolve_dropdown(client, "supplier_payment_terms_ref_id")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Batch create Direct Purchase Bookings")
    parser.add_argument("--token",         default="",          help="ERP JWT token")
    parser.add_argument("--tenant",        default=DEFAULT_TENANT, help="Tenant name")
    parser.add_argument("--count",         type=int, default=1, help="Number of PBs to create")
    parser.add_argument("--items-per-pb",  type=int, default=0, help="Line items per PB from the range pool (0 = all items in range, the default)")
    parser.add_argument("--item-range",    default="58-77", help="Pin item ID range e.g. 58-77 (uses all in range per PB, default 58-77)")
    parser.add_argument("--supplier",      type=int, default=None, help="Pin supplier ID (random if omitted)")
    parser.add_argument("--dry-run",       action="store_true", help="Print payloads without creating")
    parser.add_argument("--delay",         type=float, default=0.5, help="Delay between creates (s)")
    args = parser.parse_args()

    token = args.token or os.environ.get("ERP_TOKEN", "")
    if not token:
        print("ERROR: No token provided. Use --token or set ERP_TOKEN env var.")
        sys.exit(1)

    client = RhythmERPAPIClient()
    client.login_from_browser(token=token, tenant_id=args.tenant)
    api = PBAPIUtils(client)

    print(f"\nTenant: {args.tenant}")
    print("Resolving live FK data from ERP...")

    # ── Suppliers ─────────────────────────────────────────────────────────────
    if args.supplier is not None:
        supplier_pool = [{"id": args.supplier, "name": f"pinned:{args.supplier}"}]
        print(f"  Supplier: pinned to ID {args.supplier}")
    else:
        supplier_pool = _resolve_suppliers(client)
        if not supplier_pool:
            print("  ERROR: No suppliers found. Cannot create PBs.")
            sys.exit(1)
        print(f"  Suppliers: {len(supplier_pool)} found")

    # ── Items ─────────────────────────────────────────────────────────────────
    print("  Fetching item list...")
    item_pool = _resolve_items(client)
    if not item_pool:
        print("  ERROR: No items found. Cannot create PBs.")
        sys.exit(1)
    print(f"  Items: {len(item_pool)} found")

    # Filter to range first — avoids fetching details for every item in the listing
    if args.item_range:
        try:
            lo, hi = (int(x) for x in args.item_range.split("-"))
        except ValueError:
            print(f"  ERROR: --item-range must be like 58-77, got '{args.item_range}'")
            sys.exit(1)
        item_pool = [it for it in item_pool if lo <= it["id"] <= hi]
        if not item_pool:
            print(f"  ERROR: No items found in range {lo}-{hi}.")
            sys.exit(1)
        print(f"  Item range {lo}-{hi}: {len(item_pool)} items to fetch details for")

    # Pre-fetch item details (HSN, UOM, conversion) only for the filtered pool
    print("  Fetching item details (HSN / UOM / conversion)...")
    item_details = {}
    for it in item_pool:
        detail = _resolve_item_detail(client, it["id"])
        if detail.get("hsn_sac_no") and detail.get("alternate_uom"):
            item_details[it["id"]] = detail
            print(f"    Item {it['id']} ({it['name'][:40]}): "
                  f"HSN={detail['hsn_sac_no']} UOM={detail['alternate_uom']} "
                  f"conv={detail['uom_conversion']}")
        else:
            print(f"    Item {it['id']} ({it['name'][:40]}): skipped (missing HSN/UOM)")

    usable_items = [it for it in item_pool if it["id"] in item_details]
    if not usable_items:
        print("  ERROR: No items with HSN/UOM data. Cannot create PBs.")
        sys.exit(1)
    print(f"  Usable items: {len(usable_items)}")

    # ── Parameter dropdowns ───────────────────────────────────────────────────
    param1_ids = _resolve_dropdown(client, "parameter1") or [1]   # Division
    param2_ids = _resolve_dropdown(client, "parameter2") or [1]   # Department
    param5_ids = _resolve_dropdown(client, "parameter5") or [1]   # Location
    param6_ids = _resolve_dropdown(client, "parameter6") or [1]   # Type of Sale
    payment_term_ids = _resolve_payment_terms(client)

    print(f"  Division  (param1): {param1_ids}")
    print(f"  Department(param2): {param2_ids}")
    print(f"  Location  (param5): {param5_ids}")
    print(f"  TypeOfSale(param6): {param6_ids}")
    print(f"  Payment terms:      {payment_term_ids or 'none — will send null'}")

    # ── Build payloads ────────────────────────────────────────────────────────
    # --item-range pins the pool; --items-per-pb controls how many to pick from it.
    # Default: use all items in range (items_per_pb == len(usable_items)).
    n_lines = max(1, args.items_per_pb) if args.items_per_pb > 0 else len(usable_items)
    payloads = []
    for i in range(args.count):
        supplier      = random.choice(supplier_pool)
        payment_terms = random.choice(payment_term_ids) if payment_term_ids else None

        chosen_items = random.sample(usable_items, min(n_lines, len(usable_items)))

        lines = []
        for item in chosen_items:
            detail        = item_details[item["id"]]
            no_of_bags    = random.randint(1, 20)
            alternate_qty = round(float(no_of_bags) * random.uniform(50.0, 500.0), 2)
            rate          = round(random.uniform(10.0, 200.0), 2)
            labour        = round(random.uniform(0.0, 5.0), 2)
            disc_pct      = round(random.uniform(0.0, 5.0), 2)

            lines.append(build_direct_pb_item(
                item_ref_id=item["id"],
                hsn_sac_no=detail["hsn_sac_no"],
                alternate_uom=detail["alternate_uom"],
                uom=detail["uom"],
                uom_conversion=detail["uom_conversion"],
                rate=rate,
                no_of_bags=no_of_bags,
                alternate_qty=alternate_qty,
                empty_bag_weight=0.0,
                labour_charges=labour,
                discount_percentage=disc_pct,
            ))

        payload = build_direct_pb_payload(
            supplier_ref_id=supplier["id"],
            items=lines,
            parameter1=random.choice(param1_ids),
            parameter2=random.choice(param2_ids),
            parameter5=random.choice(param5_ids),
            parameter6=random.choice(param6_ids),
            supplier_payment_terms_ref_id=payment_terms,
        )
        payloads.append((payload, supplier, chosen_items))

    # ── Dry run ───────────────────────────────────────────────────────────────
    if args.dry_run:
        sep = "=" * 60
        print(f"\n{sep}\nDRY RUN: {args.count} Direct PB payload(s)\n{sep}")
        for i, (p, supplier, items) in enumerate(payloads):
            print(f"\n--- PB [{i + 1}/{args.count}] ---")
            print(f"  Supplier: {supplier['id']} ({supplier['name']})")
            for it in items:
                print(f"  Item:     {it['id']} ({it['name']})")
            print(f"  Lines:    {len(items)}   Total: {p['txn_currency_amount']}")
            print(json.dumps(p, indent=2, default=str))
        print("\nDry run complete. No entries created.")
        return

    # ── Create ────────────────────────────────────────────────────────────────
    sep = "=" * 60
    print(f"\n{sep}\nCreating {args.count} Direct Purchase Booking(s)...\n{sep}")

    results = []
    for i, (payload, supplier, items) in enumerate(payloads):
        try:
            data = api.create_pb(payload)
            if data:
                entry_id   = data.get("id") or data.get("entry_id")
                ref_no     = data.get("transaction_ref_no", str(entry_id))
                total      = payload["txn_currency_amount"]
                item_ids   = [it["id"] for it in items]
                results.append({"success": True, "id": entry_id, "ref": ref_no})
                print(
                    f"  [{i + 1}/{args.count}] CREATED  ID={entry_id}  ref={ref_no}"
                    f"  supplier={supplier['id']}  items={item_ids}  lines={len(items)}  total={total}"
                )
            else:
                resp   = api.last_response()
                status = api._last_status
                err    = resp.text[:300] if resp else "no response"
                results.append({"success": False, "error": err})
                print(f"  [{i + 1}/{args.count}] FAILED (HTTP {status}) — {err[:200]}")
        except Exception as e:
            results.append({"success": False, "error": str(e)})
            print(f"  [{i + 1}/{args.count}] ERROR: {e}")

        if args.delay and i < len(payloads) - 1:
            time.sleep(args.delay)

    ok = sum(1 for r in results if r.get("success"))
    print(f"\n{sep}\nDone: {ok}/{args.count} succeeded\n{sep}")
    return results


if __name__ == "__main__":
    main()

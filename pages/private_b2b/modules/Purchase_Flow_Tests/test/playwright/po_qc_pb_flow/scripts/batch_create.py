"""
batch_create.py — PO -> QC -> PB batch creation script.

Tenant: Ganesh Agrotech Pvt Ltd. (kedar@rhythmflows.com / Kedar@999999)
Flow:   Purchase Order -> Quality Check -> Purchase Booking

Usage:
    python batch_create.py --token <jwt> --tenant <id> --count 3
    python batch_create.py --token <jwt> --tenant <id> --count 1 --dry-run
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
from pages.private_b2b.modules.purchase_order.utils.api_purchase_order_utils import POAPIUtils
from pages.private_b2b.modules.quality_check.utils.api_quality_check_utils import QCAPIUtils
from pages.private_b2b.modules.purchase_booking.utils.api_purchase_booking_utils import PBAPIUtils
from pages.private_b2b.modules.Purchase_Flow_Tests.test.playwright.po_qc_pb_flow.data.po_qc_pb_data import (
    build_po_item,
    build_po_payload,
    build_qc_item,
    build_qc_payload,
    build_pb_item,
    build_pb_payload,
)

DEFAULT_TENANT = "Ganesh Agrotech Pvt Ltd."


# ── FK resolution helpers ─────────────────────────────────────────────────────

def _resolve_suppliers(client: RhythmERPAPIClient) -> list:
    try:
        resp = client.list_entries("Supplier", page_size=200)
        rows = resp.get("screenmatlistingdata_set") or []
        return [{"id": int(r["id"]), "name": str(r.get("name", ""))} for r in rows if r.get("id")]
    except Exception:
        return []


def _resolve_supplier_addresses(client: RhythmERPAPIClient, supplier_id: int) -> dict:
    try:
        detail = client.get_entry("Supplier", supplier_id)
        children = detail.get("children") or []
        ship_from = None
        bill_from = None
        payment_terms = None
        delivery_terms = None

        for stepper in children:
            name = (stepper.get("stepper_name") or "").lower()
            if "address" in name:
                addr_list = stepper.get("details") or []
                if len(addr_list) >= 1 and addr_list[0].get("id"):
                    ship_from = int(addr_list[0]["id"])
                if len(addr_list) >= 2 and addr_list[1].get("id"):
                    bill_from = int(addr_list[1]["id"])
            elif "additional" in name:
                payment_terms = stepper.get("payment_terms_ref_id")
                delivery_terms = stepper.get("delivery_terms_ref_id")

        return {
            "ship_from": ship_from,
            "bill_from": bill_from,
            "payment_terms": int(payment_terms) if payment_terms else None,
            "delivery_terms": int(delivery_terms) if delivery_terms else None,
        }
    except Exception:
        return {}


def _resolve_items(client: RhythmERPAPIClient) -> list:
    try:
        resp = client.list_entries("Item Master", page_size=200)
        rows = resp.get("screenmatlistingdata_set") or []
        return [{"id": int(r["id"]), "name": str(r.get("name", ""))} for r in rows if r.get("id")]
    except Exception:
        return []


def _resolve_item_detail(client: RhythmERPAPIClient, item_id: int) -> dict:
    try:
        d = client.get_entry("Item Master", item_id)
        return {
            "hsn_sac_no": d.get("hsn_sac_code"),
            "alternate_uom": d.get("uom"),
            "uom": d.get("base_uom"),
            "uom_conversion": float(d.get("base_uom_conversion") or 1.0),
        }
    except Exception:
        return {}


def _sniff_po_params(api: POAPIUtils) -> dict:
    """Sniff po_item_type and parameter IDs from first existing PO."""
    defaults = {"po_item_type": 1, "param1": 1, "param2": 1, "param5": 1, "param6": 1}
    try:
        listing = api.list_pos(page_size=5)
        rows = listing.get("screenmatlistingdata_set") or listing.get("results") or []
        if rows:
            first_po = api.get_po(rows[0].get("id"))
            if first_po:
                defaults["po_item_type"] = int(first_po.get("po_item_type") or 1)
                defaults["param1"] = first_po.get("parameter1", 1)
                defaults["param2"] = first_po.get("parameter2", 1)
                defaults["param5"] = first_po.get("parameter5", 1)
                defaults["param6"] = first_po.get("parameter6", 1)
    except Exception:
        pass
    return defaults


def _sniff_quality_params(client: RhythmERPAPIClient) -> list:
    """Try to get CQP parameter IDs from existing QC. Falls back to [1, 2, 3]."""
    try:
        from pages.private_b2b.modules.quality_check.api.endpoints import build_list_url
        url = build_list_url(client.BASE_URL)
        resp = client.session.get(url, headers=client.session.headers,
                                  params={"page_number": 1, "page_size": 5}, timeout=30)
        if resp.status_code != 200:
            return [1, 2, 3]
        rows = resp.json().get("screenmatlistingdata_set") or []
        if not rows:
            return [1, 2, 3]
        from pages.private_b2b.modules.quality_check.api.endpoints import build_get_url
        qc = client.session.get(build_get_url(client.BASE_URL, rows[0]["id"]),
                                headers=client.session.headers, timeout=30).json()
        details_list = (qc.get("qc_details") or [{}])[0].get("details") or []
        ids = [d["item_quality_parameter_ref_id"] for d in details_list if d.get("item_quality_parameter_ref_id")]
        return ids if ids else [1, 2, 3]
    except Exception:
        return [1, 2, 3]


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Batch create PO -> QC -> PB chains")
    parser.add_argument("--token",   default="",             help="ERP JWT token")
    parser.add_argument("--tenant",  default=DEFAULT_TENANT, help="Tenant name or numeric ID")
    parser.add_argument("--count",          type=int,   default=1,  help="Number of PO->QC->PB chains to create")
    parser.add_argument("--items-per-chain",type=int,   default=24, help="Number of item lines per PO/QC/PB")
    parser.add_argument("--qty",            type=float, default=100, help="Quantity per line item")
    parser.add_argument("--rate",           type=float, default=None, help="Fixed rate (random 500-5000 if omitted)")
    parser.add_argument("--po-item-type", type=int, default=None, help="PO Item Type ID (auto-sniffed if omitted)")
    parser.add_argument("--dry-run", action="store_true",    help="Print payloads without creating")
    parser.add_argument("--delay",   type=float, default=0.5, help="Delay between chain creates (s)")
    args = parser.parse_args()

    token = args.token or os.environ.get("ERP_TOKEN", "")
    if not token:
        print("ERROR: No token provided. Use --token or set ERP_TOKEN env var.")
        sys.exit(1)

    client = RhythmERPAPIClient()
    client.login_from_browser(token=token, tenant_id=args.tenant)
    po_api = POAPIUtils(client)
    qc_api = QCAPIUtils(client)
    pb_api = PBAPIUtils(client)

    print(f"\nTenant: {args.tenant}")
    print("Resolving live FK data from ERP...")

    # ── Suppliers ─────────────────────────────────────────────────────────────
    supplier_pool = _resolve_suppliers(client)
    if not supplier_pool:
        print("  ERROR: No suppliers found.")
        sys.exit(1)
    print(f"  Suppliers: {len(supplier_pool)} found")

    print("  Fetching supplier addresses...")
    supplier_details = {}
    for sup in supplier_pool:
        addrs = _resolve_supplier_addresses(client, sup["id"])
        if addrs.get("ship_from") and addrs.get("bill_from"):
            supplier_details[sup["id"]] = addrs
            print(f"    {sup['id']} ({sup['name'][:40]}): "
                  f"ship={addrs['ship_from']} bill={addrs['bill_from']} pay={addrs['payment_terms']}")
        else:
            print(f"    {sup['id']} ({sup['name'][:40]}): skipped (no addresses)")

    usable_suppliers = [s for s in supplier_pool if s["id"] in supplier_details]
    if not usable_suppliers:
        print("  ERROR: No suppliers with address data.")
        sys.exit(1)

    # ── Items ─────────────────────────────────────────────────────────────────
    print("  Fetching items...")
    item_pool = _resolve_items(client)
    if not item_pool:
        print("  ERROR: No items found.")
        sys.exit(1)

    item_details = {}
    for it in item_pool:
        d = _resolve_item_detail(client, it["id"])
        if d.get("hsn_sac_no") and d.get("alternate_uom"):
            item_details[it["id"]] = d
    usable_items = [it for it in item_pool if it["id"] in item_details]
    if not usable_items:
        print("  ERROR: No items with HSN/UOM data.")
        sys.exit(1)
    print(f"  Items: {len(usable_items)} usable")

    # ── PO params ─────────────────────────────────────────────────────────────
    po_params = _sniff_po_params(po_api)
    if args.po_item_type:
        po_params["po_item_type"] = args.po_item_type
    print(f"  PO Item Type: {po_params['po_item_type']}  params: "
          f"p1={po_params['param1']} p2={po_params['param2']} "
          f"p5={po_params['param5']} p6={po_params['param6']}")

    # ── QC quality params ─────────────────────────────────────────────────────
    quality_param_ids = _sniff_quality_params(client)
    print(f"  Quality param IDs: {quality_param_ids}")

    # ── Build chain payloads ──────────────────────────────────────────────────
    n_items = min(args.items_per_chain, len(usable_items))
    qty     = args.qty
    chains  = []

    for _ in range(args.count):
        supplier    = random.choice(usable_suppliers)
        sup_det     = supplier_details[supplier["id"]]
        picked      = random.sample(usable_items, n_items)

        po_lines  = []
        qc_lines  = []
        pb_lines  = []

        for item in picked:
            item_det = item_details[item["id"]]
            rate     = args.rate if args.rate else round(random.uniform(500.0, 5000.0), 2)

            po_lines.append(build_po_item(
                item_ref_id=item["id"],
                hsn_sac_no=item_det["hsn_sac_no"],
                alternate_uom=item_det["alternate_uom"],
                uom=item_det["uom"],
                uom_conversion=item_det["uom_conversion"],
                rate=rate,
                alternate_quantity=qty,
                is_gst_set_off=True,
                tax_rate=5.0,
            ))
            qc_lines.append(build_qc_item(
                item_ref_id=item["id"],
                hsn_sac_no=item_det["hsn_sac_no"],
                alternate_uom=item_det["alternate_uom"],
                uom=item_det["uom"],
                uom_conversion=item_det["uom_conversion"],
                grn_qty=qty,
                base_rate=rate,
                quality_param_ids=quality_param_ids,
            ))
            pb_lines.append(build_pb_item(
                item_ref_id=item["id"],
                hsn_sac_no=item_det["hsn_sac_no"],
                alternate_uom=item_det["alternate_uom"],
                uom=item_det["uom"],
                uom_conversion=item_det["uom_conversion"],
                rate=rate,
                alternate_qty=qty,
            ))

        po_payload = build_po_payload(
            supplier_ref_id=supplier["id"],
            items=po_lines,
            po_item_type=po_params["po_item_type"],
            parameter1=po_params["param1"],
            parameter2=po_params["param2"],
            parameter5=po_params["param5"],
            parameter6=po_params["param6"],
            supplier_payment_terms=sup_det.get("payment_terms"),
            supplier_delivery_terms=sup_det.get("delivery_terms"),
            supplier_ship_from=sup_det.get("ship_from"),
            supplier_bill_from=sup_det.get("bill_from"),
        )

        chains.append({
            "supplier": supplier,
            "picked": picked,
            "n_items": n_items,
            "po_payload": po_payload,
            "qc_lines": qc_lines,
            "pb_lines": pb_lines,
            "po_params": po_params,
            "sup_det": sup_det,
        })

    # ── Dry run ───────────────────────────────────────────────────────────────
    if args.dry_run:
        sep = "=" * 60
        print(f"\n{sep}\nDRY RUN: {args.count} PO->QC->PB chain(s)  ({n_items} items/chain)\n{sep}")
        for i, ch in enumerate(chains):
            sup = ch["supplier"]
            print(f"\n--- Chain [{i + 1}/{args.count}] ---")
            print(f"  Supplier: {sup['id']} ({sup['name']})")
            print(f"  Items ({n_items}): {[it['id'] for it in ch['picked']]}")
            print(f"\n  PO payload:")
            print(json.dumps(ch["po_payload"], indent=4, default=str))
            print(f"\n  QC lines ({len(ch['qc_lines'])}):")
            print(json.dumps(ch["qc_lines"], indent=4, default=str))
            print(f"\n  PB lines ({len(ch['pb_lines'])}):")
            print(json.dumps(ch["pb_lines"], indent=4, default=str))
        print("\nDry run complete. No entries created.")
        return

    # ── Create chains ─────────────────────────────────────────────────────────
    sep = "=" * 60
    print(f"\n{sep}\nCreating {args.count} PO->QC->PB chain(s)  ({n_items} items/chain)...\n{sep}")

    n_created = 0
    n_failed  = 0

    for i, ch in enumerate(chains):
        sup   = ch["supplier"]
        label = f"[{i + 1}/{args.count}]"

        try:
            # ── Step 1: PO ────────────────────────────────────────────────────
            po_data = po_api.create_po(ch["po_payload"])
            if not po_data:
                status = po_api._last_status
                err = (po_api._last_response.text[:300] if po_api._last_response else "no response")
                print(f"  {label} FAILED PO (HTTP {status}) - {err[:200]}")
                n_failed += 1
                continue

            po_id  = po_data.get("id") or po_data.get("entry_id")
            po_ref = po_data.get("transaction_ref_no", str(po_id))
            print(f"  {label} PO CREATED  ID={po_id} ref={po_ref}  supplier={sup['id']}  items={n_items}")

            # ── Step 2: QC ────────────────────────────────────────────────────
            qc_p = build_qc_payload(
                supplier_ref_id=sup["id"],
                po_ref_id=po_id,
                item_type_ref_id=ch["po_params"]["po_item_type"],
                items=ch["qc_lines"],
                parameter1=ch["po_params"]["param1"],
                parameter2=ch["po_params"]["param2"],
                parameter5=ch["po_params"]["param5"],
                parameter6=ch["po_params"]["param6"],
            )
            qc_data = qc_api.create_qc(payload=qc_p)
            if not qc_data:
                status = qc_api._last_status
                err = (qc_api._last_response.text[:300] if qc_api._last_response else "no response")
                print(f"  {label} FAILED QC (HTTP {status}) - {err[:200]}")
                n_failed += 1
                continue

            qc_id  = qc_data.get("id") or qc_data.get("entry_id")
            qc_ref = qc_data.get("transaction_ref_no", str(qc_id))
            print(f"  {label} QC CREATED  ID={qc_id} ref={qc_ref}")

            # ── Step 3: PB ────────────────────────────────────────────────────
            pb_p = build_pb_payload(
                qc_ref_id=qc_id,
                po_ref_id=po_id,
                supplier_ref_id=sup["id"],
                items=ch["pb_lines"],
                supplier_payment_terms_ref_id=ch["sup_det"].get("payment_terms"),
                parameter1=ch["po_params"]["param1"],
                parameter2=ch["po_params"]["param2"],
                parameter5=ch["po_params"]["param5"],
                parameter6=ch["po_params"]["param6"],
            )
            pb_data = pb_api.create_pb(pb_p)
            if not pb_data:
                status = pb_api._last_status
                err = (pb_api._last_response.text[:300] if pb_api._last_response else "no response")
                print(f"  {label} FAILED PB (HTTP {status}) - {err[:200]}")
                n_failed += 1
                continue

            pb_id  = pb_data.get("id") or pb_data.get("entry_id")
            pb_ref = pb_data.get("transaction_ref_no", str(pb_id))
            print(f"  {label} PB CREATED  ID={pb_id} ref={pb_ref}")
            print(f"  {label} CREATED #{pb_id} - Chain: PO={po_ref} -> QC={qc_ref} -> PB={pb_ref}")
            n_created += 1

        except Exception as e:
            print(f"  {label} ERROR: {e}")
            n_failed += 1

        if args.delay and i < len(chains) - 1:
            time.sleep(args.delay)

    print(f"\n{sep}\nDone: {n_created}/{args.count} chains succeeded ({n_failed} failed)\n{sep}")


if __name__ == "__main__":
    main()

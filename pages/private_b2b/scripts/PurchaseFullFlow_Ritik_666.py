"""
PurchaseFullFlow_Ritik_666.py
------------------------------
Hardcoded concurrency stress test for Ritik's local tenant 666.

Skips all discovery/CBR/schema API calls — uses known tenant-666 IDs directly.
Expected run time: ~2 min (doc creation only, no discovery overhead).

Usage:
    python -m pages.private_b2b.scripts.PurchaseFullFlow_Ritik_666

Steps:
    1. Prompts for JWT token.
    2. Creates PO → GP → GRN → QC with hardcoded tenant-666 IDs.
    3. Fires N identical PB payloads simultaneously against the same QC.
    4. Reports each PB's creation result and full accounting event log.
"""

import copy
import os
import sys
import threading
import time
from datetime import date

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

# ── Tenant-666 hardcoded IDs ──────────────────────────────────────────────────
TENANT              = "666"
N                   = 3       # parallel PB submissions

SUPPLIER_REF_ID     = 2560    # LMN
SUPPLIER_SHIP_FROM  = 3108
SUPPLIER_BILL_FROM  = 3109
ITEM_REF_ID         = 65      # Preform
ITEM_TYPE_REF_ID    = 1       # Raw material
HSN_SAC_NO          = 4
ALTERNATE_UOM       = 10
BASE_UOM            = 10
PO_TYPE             = 24
PO_ITEM_TYPE        = 1
BASE_CURRENCY       = 8
TXN_CURRENCY        = 8
PAYMENT_TERMS       = 549
DELIVERY_TERMS      = 130
PACKING_FORWARDING  = 89
DELIVERY_TYPE       = 29      # Spot
PARAMETER1          = 1
PARAMETER2          = 1
PARAMETER5          = 1
PARAMETER6          = 1
PB_PAYMENT_TERMS    = 549
QC_PARAMS           = [4, 7, 11]

# ── Item / PB amounts ─────────────────────────────────────────────────────────
QTY         = 578.0
RATE        = 3809.94
AMOUNT      = round(QTY * RATE, 6)        # 2_202_145.32
TAX_RATE    = 1.0                          # IGST %
IGST        = round(AMOUNT * TAX_RATE / 100.0, 6)   # 110_107.266
TOTAL       = round(AMOUNT + IGST, 6)     # 2_312_252.586


def build_pb_payload(po_id: int, grn_id: int, qc_id: int) -> dict:
    return {
        "transaction_date": date.today().isoformat(),
        "is_tds_applicable": False,
        "transaction_ref_no": None,
        "supplier_ref_id": SUPPLIER_REF_ID,
        "supplier_ref_type": "Supplier",
        "tax_registration_status": "Registered",
        "qc_ref_id_id": qc_id,
        "grn_ref_id_id": grn_id,
        "po_ref_id_id": po_id,
        "booking_status": "Pending",
        "so_ref_id": None,
        "parameter1": PARAMETER1,
        "parameter2": PARAMETER2,
        "parameter5": PARAMETER5,
        "parameter6": PARAMETER6,
        "posting_status": None,
        "supplier_payment_terms_ref_id": PB_PAYMENT_TERMS,
        "txn_currency": TXN_CURRENCY,
        "txn_currency_amount": AMOUNT,
        "purchase_booking_ref_type": 144,
        "section_ref_id": "0",
        "tds_percent_applicable": None,
        "tds_amount": None,
        "txn_currency_total_amount": TOTAL,
        "round_off_credit_amount": None,
        "round_off_debit_amount": None,
        "remark": None,
        "base_currency": BASE_CURRENCY,
        "conversion_rate": "1.000000",
        "txn_currency_discount_amount": 0.0,
        "grn_details": [],
        "qc_summary": {},
        "item_quality_parameter_ref_id": None,
        "type_of_bags_ref_id": None,
        "other_charges": {
            "agent_ref_id": None,
            "is_rate_percentage": False,
            "agent_commision": None,
            "agent_commision_amount": None,
        },
        "omitted_fields": [],
        "purchase_booking_details": [
            {
                "item_ref_id": ITEM_REF_ID,
                "alternate_uom": ALTERNATE_UOM,
                "hsn_sac_no": HSN_SAC_NO,
                "uom_conversion": 1.0,
                "base_rate": RATE,
                "alternate_gate_pass_quantity": QTY,
                "grn_alternate_rejected_qty": 0.0,
                "alternate_qty": QTY,
                "total_amount": AMOUNT,
                "no_of_bags": 1,
                "empty_bag_weight": 0.0,
                "alternate_net_qty": QTY,
                "uom": BASE_UOM,
                "net_of_empty_bag_amount": AMOUNT,
                "alternate_deduction_weight": 0.0,
                "alternate_c_d_deduction": 0.0,
                "qc_alternate_rejected_qty": 0.0,
                "alternate_net_purchase_qty": 0.0,
                "empty_bags_txn_amount": 0.0,
                "qc_deduction_amount": 0.0,
                "transaction_amount_without_discount": AMOUNT,
                "discount_percentage": 0.0,
                "txn_currency_discount_amount_details": 0.0,
                "txn_currency_amount_detail": AMOUNT,
                "tax_rate": TAX_RATE,
                "gst_type": "IGST",
                "txn_currency_igst_rate": TAX_RATE,
                "txn_currency_igst_amount": IGST,
                "txn_currency_cgst_rate": None,
                "txn_currency_cgst_amount": 0.0,
                "txn_currency_sgst_rate": None,
                "txn_currency_sgst_amount": 0.0,
                "txn_currency_tax_amount": IGST,
                "labour_charges": 0.0,
                "transport": 0.0,
                "advance_paid": None,
                "txn_currency_total_txn_amount": TOTAL,
                "rate": RATE,
            }
        ],
    }


def run():
    import getpass
    token = getpass.getpass("Paste your ERP JWT token: ").strip()
    if not token:
        print("ERROR: token cannot be empty.")
        sys.exit(1)

    from common.erp_api_client import RhythmERPAPIClient
    from pages.private_b2b.scripts.purchase_chain import PurchaseChain
    from pages.private_b2b.scripts.chain_context import ChainContext
    from pages.private_b2b.modules.purchase_booking.utils.api_purchase_booking_utils import PBAPIUtils

    # Step 1 — create PO → GP → GRN → QC with hardcoded IDs (no discovery)
    print(f"Step 1: creating PO → GP → GRN → QC on tenant {TENANT} (hardcoded IDs, no discovery)...")
    chain = PurchaseChain(token=token, tenant=TENANT, delay=0)

    # Inject pre-built context — skips all ERP schema/discovery API calls
    chain._context = ChainContext(
        supplier_ref_id    = SUPPLIER_REF_ID,
        item_ref_id        = ITEM_REF_ID,
        item_type_ref_id   = ITEM_TYPE_REF_ID,
        hsn_sac_no         = HSN_SAC_NO,
        alternate_uom      = ALTERNATE_UOM,
        base_uom           = BASE_UOM,
        po_type            = PO_TYPE,
        base_currency      = BASE_CURRENCY,
        txn_currency       = TXN_CURRENCY,
        parameter1         = PARAMETER1,
        parameter2         = PARAMETER2,
        parameter5         = PARAMETER5,
        parameter6         = PARAMETER6,
        payment_terms      = PAYMENT_TERMS,
        delivery_terms     = DELIVERY_TERMS,
        packing_forwarding = PACKING_FORWARDING,
        supplier_ship_from = SUPPLIER_SHIP_FROM,
        supplier_bill_from = SUPPLIER_BILL_FROM,
        delivery_type      = DELIVERY_TYPE,
        supplier_ref_type  = "Supplier",
        pb_payment_terms   = PB_PAYMENT_TERMS,
        quality_parameters = [{"item_quality_parameter_ref_id": p, "actual_value": 1} for p in QC_PARAMS],
    )


    result = chain.run(documents=["PO", "GP", "GRN", "QC"])
    po_id  = (result.get("po") or {}).get("id")
    grn_id = (result.get("grn") or {}).get("id")
    qc_id  = (result.get("qc") or {}).get("id")
    print(f"  PO={po_id}  GRN={grn_id}  QC={qc_id}\n")

    if not all([po_id, grn_id, qc_id]):
        print("ERROR: chain did not complete — check logs above.")
        sys.exit(1)

    payload = build_pb_payload(po_id, grn_id, qc_id)
    print(f"  PB payload: supplier={SUPPLIER_REF_ID}  item={ITEM_REF_ID}  qty={QTY}  rate={RATE}")
    print(f"             amount={AMOUNT}  IGST={IGST}  total={TOTAL}\n")

    # Step 2 — fire N identical PB payloads simultaneously
    results: dict = {}
    errors: dict  = {}

    def fire_pb(idx: int):
        try:
            client = RhythmERPAPIClient()
            client.login_from_browser(token=token, tenant_id=TENANT)
            api = PBAPIUtils(client)
            data, sub_id = api.create_pb(copy.deepcopy(payload))
            events = []
            if sub_id:
                for ev in api.stream_pb_events(sub_id, timeout=40):
                    events.append({
                        "step":    ev.get("step", ""),
                        "status":  ev.get("status", ""),
                        "message": ev.get("message", ""),
                    })
                    if ev.get("is_terminal"):
                        break
            results[idx] = {"data": data, "events": events}
        except Exception:
            import traceback
            errors[idx] = traceback.format_exc()

    print(f"Step 2: firing {N} identical PB payloads (QC={qc_id}, GRN={grn_id}, PO={po_id}) simultaneously...")
    start = time.time()
    threads = [threading.Thread(target=fire_pb, args=(i,)) for i in range(N)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    elapsed = time.time() - start
    print(f"Done in {elapsed:.1f}s\n")

    created = 0
    rejected = 0
    for i in range(N):
        if i in errors:
            print(f"PB {i + 1}: ERROR\n  {errors[i][:400]}")
            rejected += 1
        else:
            r = results[i]
            d = r["data"]
            if d:
                print(f"PB {i + 1}: CREATED  id={d.get('id')}  status={d.get('status')}")
                created += 1
            else:
                print(f"PB {i + 1}: REJECTED (null response)")
                rejected += 1
            for ev in r["events"]:
                flag = "!!!" if ev["status"] == "FAILED" else "   "
                print(f"  {flag} [{ev['step']}] {ev['status']}: {ev['message']}")
        print()

    print(f"Result: {created} created, {rejected} rejected out of {N} simultaneous submissions")
    if created > 1:
        print("WARNING: ERP accepted duplicate PBs against the same QC/GRN/PO — no deduplication guard.")


if __name__ == "__main__":
    run()

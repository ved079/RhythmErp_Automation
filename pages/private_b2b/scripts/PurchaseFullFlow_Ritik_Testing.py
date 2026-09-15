"""
PurchaseFullFlow_Ritik_Testing.py
----------------------------------
Concurrency stress test: fires the SAME PB payload N times simultaneously
against the ERP to verify whether duplicate Purchase Bookings are created
for the same QC/GRN/PO reference.

Finding: ERP has zero duplicate protection at the PB level.
Same QC/GRN/PO can be booked N times simultaneously — all succeed,
all accounting entries posted (N× the amounts in the ledger).

Usage:
    python -m pages.private_b2b.scripts.PurchaseFullFlow_Ritik_Testing

Steps:
    1. Runs a full chain (PO → GP → GRN → QC) to get valid document IDs.
    2. Fires N identical PB payloads against those IDs simultaneously.
    3. Reports each PB's creation result and full accounting event log.
"""

import copy
import os
import sys
import threading
import time

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

TENANT = "871"
N      = 3    # number of parallel PB submissions


def run():
    import getpass
    token = getpass.getpass("Paste your ERP JWT token: ").strip()
    if not token:
        print("ERROR: token cannot be empty.")
        sys.exit(1)

    tenant = input(f"Tenant ID [{TENANT}]: ").strip() or TENANT

    from common.erp_api_client import RhythmERPAPIClient
    from pages.private_b2b.scripts.purchase_chain import PurchaseChain, _pb_items_from_qc
    from pages.private_b2b.modules.purchase_booking.utils.api_purchase_booking_utils import PBAPIUtils

    # Step 1 — build chain up to QC
    print("Step 1: running PO → GP → GRN → QC chain to get document IDs...")
    chain = PurchaseChain(token=token, tenant=tenant, delay=0)
    result = chain.run(documents=["PO", "GP", "GRN", "QC"])
    po_id  = (result.get("po") or {}).get("id")
    grn_id = (result.get("grn") or {}).get("id")
    qc_id  = (result.get("qc") or {}).get("id")
    ctx    = result.get("ctx")
    qc_data = (result.get("qc") or {}).get("data") or {}
    print(f"  PO={po_id}  GRN={grn_id}  QC={qc_id}")
    print(f"  supplier={ctx.supplier_ref_id if ctx else '?'}  item={ctx.item_ref_id if ctx else '?'}  currency={ctx.txn_currency if ctx else '?'}\n")

    # Build PB payload dynamically from the chain context and actual QC line items
    qc_items = qc_data.get("qc_details") or []
    pb_items = _pb_items_from_qc(qc_items, ctx=ctx)
    txn_amount_total = round(sum(float(it.get("txn_currency_amount_detail") or 0.0) for it in pb_items), 6)
    discount_total   = round(sum(float(it.get("txn_currency_discount_amount_details") or 0.0) for it in pb_items), 6)
    total_with_tax   = round(sum(float(it.get("txn_currency_total_txn_amount") or 0.0) for it in pb_items), 6)

    from datetime import date
    payload = {
        "transaction_date": date.today().isoformat(),
        "is_tds_applicable": False,
        "transaction_ref_no": None,
        "supplier_ref_id": ctx.supplier_ref_id if ctx else None,
        "supplier_ref_type": ctx.supplier_ref_type if ctx else "Supplier",
        "tax_registration_status": "Registered",
        "qc_ref_id_id": qc_id,
        "grn_ref_id_id": grn_id,
        "po_ref_id_id": po_id,
        "booking_status": "Pending",
        "so_ref_id": None,
        "parameter6": ctx.parameter6 if ctx else 1,
        "parameter2": ctx.parameter2 if ctx else 1,
        "posting_status": None,
        "parameter1": ctx.parameter1 if ctx else 1,
        "parameter5": ctx.parameter5 if ctx else 1,
        "supplier_payment_terms_ref_id": ctx.pb_payment_terms if ctx else None,
        "txn_currency": ctx.txn_currency if ctx else 8,
        "txn_currency_amount": txn_amount_total,
        "purchase_booking_ref_type": 144,
        "section_ref_id": "0",
        "tds_percent_applicable": None,
        "tds_amount": None,
        "txn_currency_total_amount": total_with_tax,
        "round_off_credit_amount": None,
        "round_off_debit_amount": None,
        "remark": None,
        "base_currency": ctx.base_currency if ctx else 8,
        "conversion_rate": "1.000000",
        "txn_currency_discount_amount": discount_total,
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
        "purchase_booking_details": pb_items,
    }

    # Step 2 — fire N identical PB payloads simultaneously
    results: dict = {}
    errors: dict  = {}

    def fire_pb(idx: int):
        try:
            client = RhythmERPAPIClient()
            client.login_from_browser(token=token, tenant_id=tenant)
            api = PBAPIUtils(client)
            data, sub_id = api.create_pb(copy.deepcopy(payload))
            events = []
            if sub_id:
                for ev in api.stream_pb_events(sub_id, timeout=40):
                    events.append({
                        "step": ev.get("step", ""),
                        "status": ev.get("status", ""),
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

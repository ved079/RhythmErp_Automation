"""Purchase Booking concurrency stress-test endpoint.

Runs PO→GP→GRN→QC once, then fires N identical PB payloads simultaneously.
Events are streamed in real time as each thread produces them via a queue,
so the UI can populate each PB panel independently as it progresses.
"""

import copy
import logging
import os
import queue as _queue
import sys
import threading
import time
from datetime import datetime, timezone
from typing import Generator

from api.models import PBConcurrencyTestRequest, LogEvent

logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

# Steps that are pure echo noise — suppress from the output stream
_SUPPRESS_STEPS = {
    "PURCHASE_BOOKING_SAVED",
    "INVENTORY_SUCCESS",
    "PURCHASE_BOOKING_ACCOUNTING_SUCCESS",
    "INVENTORY_ACCOUNTING_SUCCESS",
    "PURCHASE_BOOKING_COMPLETED",
}


def _sse(event: LogEvent) -> str:
    return f"data: {event.model_dump_json()}\n\n"


def _log(msg: str) -> str:
    return _sse(LogEvent(type="log", message=msg, timestamp=datetime.now(timezone.utc)))


def _err(msg: str) -> str:
    return _sse(LogEvent(type="error", message=msg, timestamp=datetime.now(timezone.utc)))


def pb_concurrency_stream(request: PBConcurrencyTestRequest) -> Generator[str, None, None]:
    start_ts = datetime.now(timezone.utc)
    n = max(2, min(request.parallel_count, 10))

    yield _log(f"PB Concurrency Test — chain to QC, then {n} simultaneous PB submissions")

    # ── Imports ───────────────────────────────────────────────────────────────
    try:
        from pages.private_b2b.scripts.PurchaseChain_FULL_FLOW import FullChain
        from pages.private_b2b.modules.purchase_booking.utils.api_purchase_booking_utils import PBAPIUtils
        from common.erp_api_client import RhythmERPAPIClient
        from pages.private_b2b.scripts.purchase_chain import PurchaseChain
    except ImportError as e:
        yield _err(f"Import failed: {e}")
        return

    # ── Step 1: chain to QC ───────────────────────────────────────────────────
    yield _log("Step 1 — running PO → GP → GRN → QC…")
    try:
        chain = FullChain(token=request.erp_token, tenant=request.erp_tenant_id, delay=0)

        # Tenant 666 (Ritik's local): inject hardcoded context to skip all discovery
        if request.erp_tenant_id == "666":
            from pages.private_b2b.scripts.chain_context import ChainContext
            yield _log("Tenant 666 detected — using hardcoded context (no discovery)")
            chain._context = ChainContext(
                supplier_ref_id    = 2560,
                item_ref_id        = 65,
                item_type_ref_id   = 1,
                hsn_sac_no         = 4,
                alternate_uom      = 10,
                base_uom           = 10,
                po_type            = 24,
                base_currency      = 8,
                txn_currency       = 8,
                parameter1         = 1,
                parameter2         = 1,
                parameter5         = 1,
                parameter6         = 1,
                payment_terms      = 549,
                delivery_terms     = 130,
                packing_forwarding = 89,
                supplier_ship_from = 3108,
                supplier_bill_from = 3109,
                delivery_type      = 29,
                supplier_ref_type  = "Supplier",
                pb_payment_terms   = 549,
                quality_parameters = [{"item_quality_parameter_ref_id": p, "actual_value": 1} for p in [4, 7, 11]],
            )
            ctx = chain._context
            # Pre-warm internal caches so run() skips all ERP discovery calls
            chain._categories = [{"id": ctx.item_type_ref_id, "name": "Raw material", "item_count": 1}]
            chain._item_category_map = {ctx.item_ref_id: ctx.item_type_ref_id}
            chain._tax_rates = {str(ctx.hsn_sac_no): [1.0]}
            chain._cqp_cache = {ctx.item_ref_id: ctx.quality_parameters}
            result = chain.run(num_items=1, documents=["PO", "GP", "GRN", "QC"], ctx=ctx,
                               require_tax_rate=False)
        else:
            ctx_kwargs = {}
            if request.item_category_id:
                ctx_kwargs["item_category_id"] = request.item_category_id
            ctx = chain.get_context(**ctx_kwargs)
            run_kwargs: dict = dict(num_items=1, documents=["PO", "GP", "GRN", "QC"], ctx=ctx,
                                    require_tax_rate=request.require_tax_rate)
            if request.item_ref_ids:
                run_kwargs["item_ref_ids"] = request.item_ref_ids
            result = chain.run(**run_kwargs)
    except Exception as e:
        yield _err(f"Chain (PO→QC) failed: {e}")
        return

    po  = result.get("po") or {}
    grn = result.get("grn") or {}
    qc  = result.get("qc") or {}
    po_id, grn_id, qc_id = po.get("id"), grn.get("id"), qc.get("id")
    if not (po_id and grn_id and qc_id):
        yield _err(f"Chain produced incomplete IDs — PO={po_id} GRN={grn_id} QC={qc_id}")
        return

    yield _log(f"Step 1 done — PO={po.get('ref') or po_id}  GRN={grn.get('ref') or grn_id}  QC={qc.get('ref') or qc_id}")

    # ── Build PB payload ──────────────────────────────────────────────────────
    try:
        qc_data   = chain.qc_api.get_qc(qc_id) or {}
        qc_items  = qc_data.get("qc_details") or []
        supplier_id = ctx.supplier_ref_id if ctx else request.supplier_ref_id
        pb_payload = PurchaseChain._build_pb_payload(
            supplier_ref_id=supplier_id,
            qc_id=qc_id, grn_id=grn_id, po_id=po_id,
            items=[], ctx=ctx, qc_items=qc_items,
        )
    except Exception as e:
        yield _err(f"Failed to build PB payload: {e}")
        return

    yield _log(f"PB payload ready — {len(pb_payload.get('purchase_booking_details', []))} line item(s)")
    yield _log(f"Step 2 — firing {n} identical PB payloads simultaneously…")

    # ── Real-time queue: threads push events, main loop yields SSE ────────────
    ev_queue: _queue.Queue = _queue.Queue()

    def fire_pb(idx: int):
        try:
            client = RhythmERPAPIClient()
            client.login_from_browser(token=request.erp_token, tenant_id=request.erp_tenant_id)
            api = PBAPIUtils(client)
            data, sub_id = api.create_pb(copy.deepcopy(pb_payload))

            if data and data.get("id"):
                ev_queue.put(("created", idx, data))
            else:
                ev_queue.put(("rejected", idx, None))
                ev_queue.put(("done", idx, None))
                return

            if sub_id:
                for ev in api.stream_pb_events(sub_id, timeout=40):
                    step   = ev.get("step", "")
                    status = ev.get("status", "")
                    if status != "STARTED" and step not in _SUPPRESS_STEPS:
                        ev_queue.put(("event", idx, ev))
                    if ev.get("is_terminal"):
                        break
        except Exception:
            import traceback
            ev_queue.put(("error", idx, traceback.format_exc()))
        finally:
            ev_queue.put(("done", idx, None))

    threads = [threading.Thread(target=fire_pb, args=(i,), daemon=True) for i in range(n)]
    fire_start = time.time()
    for t in threads:
        t.start()

    # Drain the queue and stream events in real time
    finished = 0
    created  = 0
    rejected = 0

    while finished < n:
        try:
            kind, idx, data = ev_queue.get(timeout=90)
        except _queue.Empty:
            yield _err("Timeout waiting for PB threads (>90 s)")
            break

        pb_label = f"PB [{idx + 1}]"

        if kind == "created":
            pb_ref = data.get("transaction_ref_no") or data.get("ref") or data.get("id")
            yield _log(f"{pb_label} CREATED — id={data.get('id')}  ref={pb_ref}  status={data.get('status')}")
            created += 1

        elif kind == "rejected":
            yield _log(f"{pb_label} REJECTED — ERP returned null/empty response")
            rejected += 1

        elif kind == "error":
            yield _err(f"{pb_label} ERROR — {data[:400]}")
            rejected += 1

        elif kind == "event":
            step      = data.get("step", "")
            status    = data.get("status", "")
            ev_type   = "error" if status == "FAILED" else "log"
            flag      = "!!!" if status == "FAILED" else "   "
            msg_sfx   = f": {data['message']}" if data.get("message") else ""
            yield _sse(LogEvent(
                type=ev_type,
                message=f"  {flag} {pb_label} [{step}] {status}{msg_sfx}",
                timestamp=datetime.now(timezone.utc),
            ))

        elif kind == "done":
            finished += 1

    for t in threads:
        t.join(timeout=5)

    elapsed_fire = time.time() - fire_start
    yield _log(f"All {n} threads finished in {elapsed_fire:.1f}s")

    total_elapsed = (datetime.now(timezone.utc) - start_ts).total_seconds()
    summary = (
        f"Done — {created} PBs created, {rejected} rejected out of {n} "
        f"simultaneous submissions ({total_elapsed:.1f}s)"
    )
    if created > 1:
        summary += f" — ⚠ DUPLICATE DETECTED: ERP accepted {created} PBs for the same QC/GRN/PO"
    elif created == 0:
        summary += " — ERP rejected all duplicates"

    yield _sse(LogEvent(
        type="run_end",
        message=summary,
        timestamp=datetime.now(timezone.utc),
        created=created,
        failed=rejected,
        total=n,
    ))

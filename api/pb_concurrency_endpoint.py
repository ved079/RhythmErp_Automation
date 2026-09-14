"""Purchase Booking concurrency stress-test endpoint.

Runs PO→GP→GRN→QC once to obtain valid document IDs, then fires N identical
PB payloads simultaneously. Streams progress via SSE so the UI can show
per-PB results and accounting events as they arrive.
"""

import copy
import logging
import os
import sys
import threading
import time
from datetime import datetime, timezone
from typing import Generator

from api.models import PBConcurrencyTestRequest, LogEvent

logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)


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

    # ── Import dependencies ───────────────────────────────────────────────────
    try:
        from pages.private_b2b.scripts.PurchaseChain_FULL_FLOW import FullChain
        from pages.private_b2b.modules.purchase_booking.utils.api_purchase_booking_utils import PBAPIUtils
        from common.erp_api_client import RhythmERPAPIClient
        from pages.private_b2b.scripts.purchase_chain import PurchaseChain
    except ImportError as e:
        yield _err(f"Import failed: {e}")
        return

    # ── Step 1: Build chain to QC ─────────────────────────────────────────────
    yield _log("Step 1 — running PO → GP → GRN → QC to get document IDs…")
    try:
        chain = FullChain(token=request.erp_token, tenant=request.erp_tenant_id, delay=0)
        ctx_kwargs = {}
        if request.item_category_id:
            ctx_kwargs["item_category_id"] = request.item_category_id
        ctx = chain.get_context(**ctx_kwargs)
        run_kwargs = dict(
            num_items=1,
            documents=["PO", "GP", "GRN", "QC"],
            ctx=ctx,
            require_tax_rate=request.require_tax_rate,
        )
        if request.item_ref_ids:
            run_kwargs["item_ref_ids"] = request.item_ref_ids
        result = chain.run(**run_kwargs)
    except Exception as e:
        yield _err(f"Chain (PO→QC) failed: {e}")
        return

    po  = result.get("po") or {}
    grn = result.get("grn") or {}
    qc  = result.get("qc") or {}
    po_id  = po.get("id")
    grn_id = grn.get("id")
    qc_id  = qc.get("id")

    if not (po_id and grn_id and qc_id):
        yield _err(f"Chain produced incomplete IDs — PO={po_id} GRN={grn_id} QC={qc_id}")
        return

    yield _log(f"Step 1 done — PO={po.get('ref') or po_id}  GRN={grn.get('ref') or grn_id}  QC={qc.get('ref') or qc_id}")

    # ── Build PB payload from QC data ────────────────────────────────────────
    yield _log("Building PB payload from QC document…")
    try:
        qc_data = chain.qc_api.get_qc(qc_id) or {}
        qc_items = qc_data.get("qc_details") or []
        supplier_id = ctx.supplier_ref_id if ctx else request.supplier_ref_id
        # items=[] is safe: _pb_items_from_qc falls back to QC line data for
        # uom_conversion and tax_rate when items list is empty.
        pb_payload = PurchaseChain._build_pb_payload(
            supplier_ref_id=supplier_id,
            qc_id=qc_id,
            grn_id=grn_id,
            po_id=po_id,
            items=[],
            ctx=ctx,
            qc_items=qc_items,
        )
    except Exception as e:
        yield _err(f"Failed to build PB payload: {e}")
        return

    yield _log(f"PB payload ready — {len(pb_payload.get('purchase_booking_details', []))} line item(s)")

    # ── Step 2: Fire N identical PBs simultaneously ───────────────────────────
    yield _log(f"Step 2 — firing {n} identical PB payloads simultaneously…")

    pb_results: dict[int, dict] = {}
    pb_errors:  dict[int, str]  = {}
    lock = threading.Lock()

    def fire_pb(idx: int):
        try:
            client = RhythmERPAPIClient()
            client.login_from_browser(token=request.erp_token, tenant_id=request.erp_tenant_id)
            api = PBAPIUtils(client)
            data, sub_id = api.create_pb(copy.deepcopy(pb_payload))
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
            with lock:
                pb_results[idx] = {"data": data, "events": events}
        except Exception:
            import traceback
            with lock:
                pb_errors[idx] = traceback.format_exc()

    threads = [threading.Thread(target=fire_pb, args=(i,), daemon=True) for i in range(n)]
    fire_start = time.time()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    elapsed_fire = time.time() - fire_start

    yield _log(f"All {n} threads joined in {elapsed_fire:.1f}s")

    # ── Emit per-PB results ───────────────────────────────────────────────────
    created = 0
    rejected = 0
    for i in range(n):
        if i in pb_errors:
            yield _err(f"PB [{i + 1}] ERROR — {pb_errors[i][:300]}")
            rejected += 1
        else:
            r = pb_results.get(i, {})
            d = r.get("data")
            if d and d.get("id"):
                pb_ref = d.get("transaction_ref_no") or d.get("ref") or d.get("id")
                yield _log(f"PB [{i + 1}] CREATED — id={d.get('id')}  ref={pb_ref}  status={d.get('status')}")
                created += 1
            else:
                yield _log(f"PB [{i + 1}] REJECTED — null/empty response (ERP may have blocked duplicate)")
                rejected += 1
            for ev in (r.get("events") or []):
                step = ev["step"]
                status = ev["status"]
                # Skip noisy: STARTED lines and *_SUCCESS echo steps
                if status == "STARTED":
                    continue
                if step.endswith("_SUCCESS") or step == "PURCHASE_BOOKING_SAVED":
                    continue
                ev_type = "error" if status == "FAILED" else "log"
                flag = "!!!" if status == "FAILED" else "   "
                msg_suffix = f": {ev['message']}" if ev.get("message") else ""
                yield _sse(LogEvent(
                    type=ev_type,
                    message=f"  {flag} PB [{i + 1}] [{step}] {status}{msg_suffix}",
                    timestamp=datetime.now(timezone.utc),
                ))

    # ── Summary ───────────────────────────────────────────────────────────────
    total_elapsed = (datetime.now(timezone.utc) - start_ts).total_seconds()
    summary = (
        f"Done — {created} PBs created, {rejected} rejected out of {n} simultaneous submissions "
        f"({total_elapsed:.1f}s)"
    )
    if created > 1:
        summary += f" — ⚠ DUPLICATE DETECTED: ERP accepted {created} PBs for the same QC/GRN/PO"
    elif created == 0:
        summary += " — ERP rejected all duplicates (good)"

    yield _sse(LogEvent(
        type="run_end",
        message=summary,
        timestamp=datetime.now(timezone.utc),
        created=created,
        failed=rejected,
        total=n,
    ))

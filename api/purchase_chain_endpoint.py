"""Purchase Chain endpoint — SSE-streamed linked PO->GP->GRN->QC creation."""

import json
import logging
import sys
import time
import os
from datetime import datetime, timezone
from typing import Generator

from api.models import PurchaseChainRequest, LogEvent

logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)


def _sse_event(event: LogEvent) -> str:
    return f"data: {event.model_dump_json()}\n\n"


def purchase_chain_stream(request: PurchaseChainRequest) -> Generator[str, None, None]:
    """Execute purchase chain(s) and stream progress as SSE events."""
    start_ts = datetime.now(timezone.utc)
    total_chains = max(1, min(request.count, 50))
    created = 0
    failed = 0

    yield _sse_event(LogEvent(
        type="log",
        message=f"Starting {total_chains} purchase chain(s) — supplier={request.supplier_ref_id}, items={request.num_items}",
        timestamp=start_ts,
    ))

    try:
        from pages.private_b2b.scripts.purchase_chain import PurchaseChain
    except ImportError as e:
        yield _sse_event(LogEvent(
            type="error",
            message=f"Failed to import PurchaseChain: {e}",
            timestamp=datetime.now(timezone.utc),
        ))
        return

    erp_token = request.erp_token
    if not erp_token:
        erp_token = os.environ.get("ERP_TOKEN", "")
    if not erp_token:
        yield _sse_event(LogEvent(
            type="error",
            message="No ERP token provided. Set ERP_TOKEN env var or pass erp_token.",
            timestamp=datetime.now(timezone.utc),
        ))
        return

    try:
        chain = PurchaseChain(
            token=erp_token,
            tenant=request.erp_tenant_id,
            delay=request.delay,
        )
    except Exception as e:
        yield _sse_event(LogEvent(
            type="error",
            message=f"Failed to initialize PurchaseChain: {e}",
            timestamp=datetime.now(timezone.utc),
        ))
        return

    # ── Pre-flight: validate and fix Accounting Definition ───────────────
    yield _sse_event(LogEvent(
        type="log",
        message="Pre-flight: validating Purchase Booking Accounting Definition…",
        timestamp=datetime.now(timezone.utc),
    ))
    try:
        from pages.private_b2b.modules.purchase_booking.utils.ad_setup import (
            fetch_coa, resolve_accounts, fetch_type_of_sale_ids,
            find_existing_pb_ad, build_ad_payload, apply_ad,
        )
        coa = fetch_coa(chain.client)
        accounts = resolve_accounts(coa)
        tos_ids = fetch_type_of_sale_ids(chain.client)
        existing = find_existing_pb_ad(chain.client)
        payload = build_ad_payload(accounts, tos_ids)
        apply_ad(chain.client, payload, existing["id"] if existing else None, dry_run=False)
        yield _sse_event(LogEvent(
            type="log",
            message=f"AD pre-flight done — {'updated' if existing else 'created'} canonical PB Accounting Definition",
            timestamp=datetime.now(timezone.utc),
        ))
    except Exception as ad_err:
        yield _sse_event(LogEvent(
            type="log",
            message=f"AD pre-flight warning: {ad_err} — continuing (chains may still work)",
            timestamp=datetime.now(timezone.utc),
        ))

    # ── Discover tenant context ──────────────────────────────────────────
    yield _sse_event(LogEvent(
        type="log",
        message="Discovering tenant reference data (suppliers, items, UOMs, dropdowns)…",
        timestamp=datetime.now(timezone.utc),
    ))
    try:
        ctx = chain.get_context(item_category_id=request.item_category_id)
        yield _sse_event(LogEvent(
            type="log",
            message=(
                f"Discovery complete — supplier={ctx.supplier_ref_id}, "
                f"item={ctx.item_ref_id}, alt_uom={ctx.alternate_uom}, "
                f"base_uom={ctx.base_uom}, po_type={ctx.po_type}, "
                f"currency={ctx.txn_currency}, delivery_type={ctx.delivery_type}, "
                f"qc_params={len(ctx.quality_parameters)}"
            ),
            timestamp=datetime.now(timezone.utc),
        ))
    except Exception as e:
        yield _sse_event(LogEvent(
            type="error",
            message=f"Context discovery failed: {e} — chain may use fallback IDs",
            timestamp=datetime.now(timezone.utc),
        ))
        ctx = None

    docs_label = " → ".join(request.documents) if request.documents else "PO → GP → GRN → QC"
    yield _sse_event(LogEvent(
        type="log",
        message=f"Documents to create: {docs_label}",
        timestamp=datetime.now(timezone.utc),
    ))

    for i in range(total_chains):
        chain_start = time.time()
        # Per-chain supplier (Q2/Option A): refresh the supplier-scoped context
        # so each chain uses its own supplier's addresses + payment terms.
        if request.supplier_ref_ids and len(request.supplier_ref_ids) == total_chains:
            chain_supplier = request.supplier_ref_ids[i]
        else:
            chain_supplier = request.supplier_ref_id
        yield _sse_event(LogEvent(
            type="log",
            message=f"Chain [{i + 1}/{total_chains}] — supplier={chain_supplier}",
            timestamp=datetime.now(timezone.utc),
        ))

        try:
            kwargs = dict(
                num_items=request.num_items,
                documents=request.documents,
            )
            # Option A: per-supplier context so addresses + payment terms are
            # resolved for the chain's own supplier, not the default one.
            kwargs["ctx"] = chain.get_context_for_supplier(chain_supplier)
            if request.multi_gate_pass:
                kwargs["multi_gate_pass"] = True
                kwargs["gp_count"] = max(1, request.gp_count)
                yield _sse_event(LogEvent(
                    type="log",
                    message=(
                        f"Multi Gate Pass ON — one PO split across "
                        f"{max(1, request.gp_count)} gate passes (each GP → its own GRN & QC)"
                    ),
                    timestamp=datetime.now(timezone.utc),
                ))
            kwargs["qc_discount"] = request.qc_discount
            kwargs["is_rate_weight_deduction"] = request.is_rate_weight_deduction
            kwargs["payment_method"] = request.payment_method
            kwargs["payment_post"] = request.payment_post
            kwargs["supplier_ref_type"] = request.supplier_ref_type
            if request.customer_ref_id is not None:
                kwargs["customer_ref_id"] = request.customer_ref_id
            # Only pass explicit overrides if the caller set them intentionally
            if chain_supplier and chain_supplier != 1:
                kwargs["supplier_ref_id"] = chain_supplier
            if request.item_ref_id and request.item_ref_id != 5:
                kwargs["item_ref_id"] = request.item_ref_id
            if request.item_ref_ids:
                kwargs["item_ref_ids"] = request.item_ref_ids
            if request.item_category_id:
                kwargs["item_category_id"] = request.item_category_id
            kwargs["require_tax_rate"] = request.require_tax_rate
            yield _sse_event(LogEvent(
                type="log",
                message=(
                    f"Config: category_id={request.item_category_id or '(auto-pick)'}, "
                    f"tax_rate={'ON' if request.require_tax_rate else 'OFF'}, "
                    f"items={list(request.item_ref_ids) if request.item_ref_ids else request.item_ref_id}"
                ),
                timestamp=datetime.now(timezone.utc),
            ))
            result = chain.run(**kwargs)
            elapsed = time.time() - chain_start
            po = result.get("po") or {}
            gp = result.get("gp") or {}
            grn = result.get("grn") or {}
            qc = result.get("qc") or {}
            pb = result.get("pb") or {}
            so = result.get("so") or {}
            parts = []
            if po.get("id"): parts.append(f"PO {po['id']}")
            gps = result.get("gps") or ([gp] if gp else [])
            grns = result.get("grns") or ([grn] if grn else [])
            qcs = result.get("qcs") or ([qc] if qc else [])
            if len(gps) > 1:
                parts.append(f"{len(gps)}×GP ({', '.join(str(g['id']) for g in gps)})")
                parts.append(f"{len(grns)}×GRN ({', '.join(str(g['id']) for g in grns)})")
                if qcs:
                    parts.append(f"{len(qcs)}×QC ({', '.join(str(q['id']) for q in qcs)})")
            else:
                if gp.get("id"): parts.append(f"GP {gp['id']}")
                if grn.get("id"): parts.append(f"GRN {grn['id']}")
                if qc.get("id"): parts.append(f"QC {qc['id']}")
            if pb.get("id"): parts.append(f"PB {pb['id']}")
            if so.get("id"): parts.append(f"SO {so['id']}")
            payment = result.get("payment") or {}
            if payment.get("id"): parts.append(f"PYMT {payment['id']}")
            yield _sse_event(LogEvent(
                type="log",
                message=f"Chain [{i + 1}] OK — {' → '.join(parts)} ({elapsed:.1f}s)",
                timestamp=datetime.now(timezone.utc),
            ))

            # ── JV check (optional) ────────────────────────────────────────
            if request.with_jv_check and pb.get("ref") and result.get("ctx"):
                yield _sse_event(LogEvent(
                    type="log",
                    message=f"JV check — verifying accounting entries for {pb['ref']}…",
                    timestamp=datetime.now(timezone.utc),
                ))
                try:
                    from pages.private_b2b.modules.journal_voucher.utils.api_jv_utils import JVAPIUtils
                    jv_ctx = result["ctx"]
                    jv_result = JVAPIUtils(chain.client).verify_pb(
                        pb_ref_no=pb["ref"],
                        division_id=jv_ctx.parameter1,
                        department_id=jv_ctx.parameter2,
                        type_of_sale_id=jv_ctx.parameter5,
                        location_id=jv_ctx.parameter6,
                    )
                    jv_status = "✓ BALANCED" if jv_result.ok() else ("✕ UNBALANCED" if jv_result.found else "✕ NOT FOUND")
                    yield _sse_event(LogEvent(
                        type="log" if jv_result.ok() else "error",
                        message=f"JV [{i + 1}] {jv_status} — {jv_result.summary()}",
                        timestamp=datetime.now(timezone.utc),
                    ))
                except Exception as jv_err:
                    yield _sse_event(LogEvent(
                        type="error",
                        message=f"JV check error: {jv_err}",
                        timestamp=datetime.now(timezone.utc),
                    ))

            created += 1
            # Allow async accounting to settle before the next chain posts its
            # inventory entries for the same items — prevents ledger lock conflicts.
            if "PB" in (request.documents or []) and i < total_chains - 1:
                time.sleep(4)
        except Exception as e:
            elapsed = time.time() - chain_start
            yield _sse_event(LogEvent(
                type="error",
                message=f"Chain [{i + 1}] FAILED after {elapsed:.1f}s: {e}",
                timestamp=datetime.now(timezone.utc),
            ))
            failed += 1

    total_elapsed = (datetime.now(timezone.utc) - start_ts).total_seconds()
    yield _sse_event(LogEvent(
        type="run_end",
        message=f"Done — {created} chains created, {failed} failed ({total_elapsed:.1f}s)",
        timestamp=datetime.now(timezone.utc),
        created=created,
        failed=failed,
        total=total_chains,
    ))

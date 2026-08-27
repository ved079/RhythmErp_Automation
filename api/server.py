"""
FastAPI backend for Rhythm ERP Test Runner UI.

Pure execution engine — only handles test running and discovery.
All auth, user management, environments, settings, and audit logging
are handled by the Next.js application.

Endpoints:
  - POST /api/runs/start    — Start a test run (returns SSE stream)
  - POST /api/runs/{id}/stop — Stop a running test
  - GET  /api/modules       — Discover test modules
  - GET  /api/screenshot    — Get browser screenshot
  - GET  /api/test-cases    — Read test case definitions
  - POST /api/batch-create  — Batch data creation (SSE stream)
  - POST /api/purchase-chain — Create linked PO->GP->GRN->QC chain (SSE stream)
  - POST /api/jv-verify      — Verify a Purchase Booking's Journal Voucher entry
  - GET  /api/master-data — List master data entries (Supplier, Item Master, etc.)
  - GET  /api/batch-create/{run_id}/export — Download Excel of batch results
  - GET  /api/health        — Health check
"""

import os
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse

from api.models import (
    ModuleListResponse, CreateRunRequest, StartRunRequest, BatchCreateRequest,
    PurchaseChainRequest, ConcurrencyDispatchRequest, CbrTokenRequest, CbrCreateLocationsRequest,
    FetchFkRequest, JVVerifyRequest, PBListRequest,
)
from api.concurrency_dispatch import dispatch_concurrent, ping_agents
from api.test_discovery import discover_all_modules
from api.test_runner import run_tests_stream, stop_run
from api.batch_create import batch_create_stream, _build_payloads_only, export_batch_excel
from api.purchase_chain_endpoint import purchase_chain_stream
from api.database import init_db
from api.screenshot_store import take_screenshot


PROJECT_ROOT = Path(__file__).parent.parent

app = FastAPI(title="Rhythm ERP Test API", version="3.0.0")

# --- CORS — restricted to frontend URL ---
_cors_origins = os.getenv("API_CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in _cors_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ================================================================
# STARTUP
# ================================================================

@app.on_event("startup")
def startup():
    init_db()


# ================================================================
# TEST DISCOVERY ENDPOINT
# ================================================================

@app.get("/api/modules", response_model=ModuleListResponse)
def get_modules():
    """Discover all test modules from the pages/ directory."""
    return discover_all_modules(str(PROJECT_ROOT))


# ================================================================
# TEST RUNS ENDPOINTS
# ================================================================

@app.post("/api/runs/start")
def start_run(request: StartRunRequest):
    """Start a test run and return SSE stream with live output."""
    run_request = CreateRunRequest(
        module=request.module,
        sub_module=request.sub_module,
        tests=request.tests,
        env_url=request.env_url,
        erp_token=request.erp_token,
        erp_tenant_id=request.erp_tenant_id,
        erp_email=request.erp_email,
        erp_password=request.erp_password,
    )

    return StreamingResponse(
        run_tests_stream(run_request),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@app.post("/api/runs/{run_id}/stop")
def stop_run_endpoint(run_id: str):
    """Stop a running test by killing the subprocess."""
    from api.database import get_run
    run_data = get_run(run_id)
    if not run_data:
        raise HTTPException(status_code=404, detail="Run not found")

    if run_data.get("status") not in ("running", "pending"):
        raise HTTPException(status_code=400, detail="Run is not currently running")

    success = stop_run(run_id)
    if success:
        return {"message": f"Run {run_id} stopped successfully", "status": "stopped"}
    else:
        raise HTTPException(status_code=400, detail="Could not stop run — process may have already finished")


# ================================================================
# SCREENSHOT ENDPOINT
# ================================================================

@app.get("/api/screenshot")
def get_screenshot_endpoint():
    """Returns the current browser screenshot as base64 PNG."""
    img = take_screenshot()
    if img is None:
        return JSONResponse({"screenshot": None, "active": False})
    return JSONResponse({"screenshot": img, "active": True})


# ================================================================
# BATCH DATA CREATION ENDPOINT
# ================================================================

@app.post("/api/batch-create")
def batch_create_endpoint(request: BatchCreateRequest):
    """Create test data records via the ERP API (SSE-streamed progress)."""
    request.count = max(1, min(request.count, 500))
    return StreamingResponse(
        batch_create_stream(request),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@app.post("/api/batch-create/preview")
def batch_preview_endpoint(request: BatchCreateRequest):
    """Generate payloads without creating them — used by conflict mode."""
    payloads = _build_payloads_only(request)
    return {"payloads": payloads}


@app.post("/api/batch-create/fetch-fk")
def fetch_fk_endpoint(request: FetchFkRequest):
    """Fetch FK dropdown options from the live ERP for a given screen."""
    from common.erp_api_client import RhythmERPAPIClient
    from common.fk_resolver import FkResolver

    client = RhythmERPAPIClient(username="", password="", tenant_id=request.erp_tenant_id)
    try:
        client.login_from_browser(token=request.erp_token, tenant_id=request.erp_tenant_id)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Auth failed: {e}")

    try:
        resolver = FkResolver(client)
        options = resolver.resolve(request.screen)
        result = [{"name": k, "id": v, "count": 0} for k, v in options.items()]

        # For Item Category: count how many Item Master records belong to each category
        if request.screen == "Item Category" and result:
            try:
                from concurrent.futures import ThreadPoolExecutor
                im_resp = client.list_entries("Item Master", page_size=500)
                im_rows = (im_resp.get("screenmatlistingdata_set") or im_resp.get("results") or []) if im_resp else []

                def _fetch_cat(row):
                    iid = row.get("id")
                    if iid is None:
                        return None
                    try:
                        det = client.get_entry("Item Master", iid)
                        return det.get("item_category") if det else None
                    except Exception:
                        return None

                with ThreadPoolExecutor(max_workers=8) as ex:
                    cat_ids = list(ex.map(_fetch_cat, im_rows))

                counts: dict[int, int] = {}
                for cat_id in cat_ids:
                    if cat_id is not None:
                        counts[int(cat_id)] = counts.get(int(cat_id), 0) + 1
                for opt in result:
                    opt["count"] = counts.get(opt["id"], 0)
            except Exception:
                pass

        return {"options": result}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch {request.screen}: {e}")


@app.post("/api/batch-create/cqp-fill-preview")
def cqp_fill_preview_endpoint(request: BatchCreateRequest):
    """Return which items are missing CQP entries — used by Fill All Items preview."""
    from common.erp_api_client import RhythmERPAPIClient
    from common.fk_resolver import FkResolver

    print(f"[CQP-PREVIEW] Request received — tenant={request.erp_tenant_id}")
    client = RhythmERPAPIClient(tenant_id=request.erp_tenant_id)
    try:
        client.login_from_browser(token=request.erp_token, tenant_id=request.erp_tenant_id)
        print(f"[CQP-PREVIEW] Auth OK")
    except Exception as e:
        print(f"[CQP-PREVIEW] Auth failed: {e}")
        return {"error": str(e), "missing": [], "total_items": 0, "existing_count": 0}

    try:
        # Resolve all item IDs
        resolver = FkResolver(client)
        item_id_map = resolver.resolve("Item Master", parent_screen="Commodity Quality Parameter", field_key="item_ref_id") or {}
        print(f"[CQP-PREVIEW] Resolved {len(item_id_map)} items from FK resolver")

        # Reverse map: id → name
        id_to_name = {v: k for k, v in item_id_map.items()}

        # Fetch existing CQP entries
        existing = client.list_entries("Commodity Quality Parameter", page_size=500)
        existing_rows = existing.get("screenmatlistingdata_set", existing.get("results", []))
        print(f"[CQP-PREVIEW] Found {len(existing_rows)} existing CQP listing rows")

        # Get used item IDs by fetching each entry's detail
        used_ids: set = set()
        for row in existing_rows:
            entry_id = row.get("id")
            if entry_id:
                detail = client.get_entry("Commodity Quality Parameter", entry_id)
                if detail:
                    iid = detail.get("item_ref_id")
                    if iid is not None:
                        try:
                            used_ids.add(int(iid))
                        except (ValueError, TypeError):
                            pass

        print(f"[CQP-PREVIEW] {len(used_ids)} used item IDs: {sorted(used_ids)}")

        missing = [
            {"id": iid, "name": id_to_name.get(iid, f"Item #{iid}")}
            for iid in sorted(item_id_map.values())
            if iid not in used_ids
        ]
        return {
            "total_items": len(item_id_map),
            "existing_count": len(used_ids),
            "missing": missing,
        }
    except Exception as e:
        import traceback
        print(f"[CQP-PREVIEW] ERROR: {e}\n{traceback.format_exc()}")
        return {"error": str(e), "missing": [], "total_items": 0, "existing_count": 0}
    finally:
        try:
            client.close()
        except Exception:
            pass


@app.post("/api/batch-create/cbr-locations")
def cbr_locations_endpoint(request: CbrTokenRequest):
    """Return all locations with occupied status for CBR batch create."""
    from pages.commodity_settings.modules.commodity_base_rate.data.cbr_data import LOCATION_ID_MAP
    fallback = [{"id": lid, "name": name, "occupied": False} for name, lid in LOCATION_ID_MAP.items()]
    try:
        from common.erp_api_client import RhythmERPAPIClient
        client = RhythmERPAPIClient(tenant_id=request.erp_tenant_id)
        client.login_from_browser(token=request.erp_token, tenant_id=request.erp_tenant_id)

        # Get all locations from CBR schema dropdown
        locations = []
        schema = client.get_screen_schema("Commodity Base Rate")
        if schema:
            fields = client._flatten_fields(schema.get("screendefinition_set", []))
            for field in fields:
                if field.get("field_key") == "location_ref_id":
                    opts = field.get("filter_dropdown_raw_query", [])
                    if isinstance(opts, list):
                        for opt in opts:
                            opt_id = opt.get("id")
                            opt_key = opt.get("key")
                            if opt_id and opt_key:
                                locations.append({"id": int(opt_id), "name": opt_key, "occupied": False})
                    break

        if not locations:
            locations = fallback

        # Fetch current active items directly from Item Master listing
        total_item_ids: set = set()
        try:
            im_result = client.list_entries("Item Master", page_size=500)
            im_rows = im_result.get("screenmatlistingdata_set", im_result.get("results", []))
            total_item_ids = {int(r["id"]) for r in im_rows if r.get("id")}
            print(f"[CBR] {len(total_item_ids)} total items in Item Master")
        except Exception as exc:
            print(f"[CBR] item fetch failed (gap detection disabled): {exc}")

        # Check existing CBR entries and per-location item coverage
        try:
            existing = client.list_entries("Commodity Base Rate", page_size=500)
            entries = existing.get("screenmatlistingdata_set", existing.get("results", []))
            name_to_id = {loc["name"].lower(): loc["id"] for loc in locations}

            # Group ALL entries by location (union across multiple entries per location)
            entries_by_loc_id: dict = {}
            for e in (entries or []):
                loc_val = e.get("location_ref_id")
                if loc_val is None:
                    continue
                loc_id = None
                if isinstance(loc_val, (int, float)):
                    loc_id = int(loc_val)
                elif isinstance(loc_val, str):
                    try:
                        loc_id = int(loc_val)
                    except (ValueError, TypeError):
                        loc_id = name_to_id.get(loc_val.lower().strip())
                if loc_id is not None:
                    entries_by_loc_id.setdefault(loc_id, []).append(e)

            # For each location, union item_ref_ids across ALL its CBR entries
            for loc in locations:
                lid = loc["id"]
                if lid not in entries_by_loc_id:
                    loc["gap_count"] = len(total_item_ids)
                    continue

                covered_item_ids: set = set()
                if total_item_ids:
                    for entry in entries_by_loc_id[lid]:
                        try:
                            detail = client.get_entry("Commodity Base Rate", entry["id"])
                            for child in (detail or {}).get("children", []):
                                for row in child.get("details", []):
                                    iid = row.get("item_ref_id")
                                    if iid is not None:
                                        covered_item_ids.add(int(iid))
                        except Exception:
                            pass

                gap = len(total_item_ids - covered_item_ids)
                loc["gap_count"] = gap
                if gap == 0:
                    loc["occupied"] = True

        except Exception as exc:
            print(f"[CBR] occupied detection failed: {exc}")

        occupied_count = sum(1 for loc in locations if loc["occupied"])
        return {
            "locations": locations,
            "occupied_count": occupied_count,
            "available_count": len(locations) - occupied_count,
        }
    except Exception as e:
        print(f"[CBR] locations fetch failed: {e}")
        return {"locations": fallback, "occupied_count": 0, "available_count": len(fallback)}


@app.post("/api/batch-create/cbr-create-locations")
def cbr_create_locations_endpoint(request: CbrCreateLocationsRequest):
    """Create new Location entries in the ERP for CBR batch create."""
    created = []
    failed = []
    try:
        from common.erp_api_client import RhythmERPAPIClient
        client = RhythmERPAPIClient(tenant_id=request.erp_tenant_id)
        client.login_from_browser(token=request.erp_token, tenant_id=request.erp_tenant_id)

        for item in request.locations:
            payload = {
                "id": "",
                "attribute_name": "Location",
                "name": item.name,
                "description": None,
                "details": [],
                "children": [],
            }
            try:
                result = client.create_entry(payload)
                if result and result.get("id"):
                    created.append({"id": result["id"], "name": item.name})
                else:
                    failed.append({"name": item.name, "error": "No ID in response"})
            except Exception as e:
                failed.append({"name": item.name, "error": str(e)[:200]})

        try:
            client.close()
        except Exception:
            pass
    except Exception as e:
        for item in request.locations:
            failed.append({"name": item.name, "error": str(e)[:200]})

    return {"created": created, "failed": failed}


# ================================================================
# BATCH CREATE EXPORT ENDPOINT
# ================================================================

@app.get("/api/batch-results")
def batch_results_list():
    """List all past batch run summaries, newest first."""
    from api.batch_create import RESULTS_DIR
    import json as _json
    rows = []
    for path in sorted(RESULTS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = _json.load(f)
            rows.append({
                "run_id":         data.get("run_id", path.stem),
                "module":         data.get("module", ""),
                "sub_module":     data.get("sub_module", ""),
                "total":          data.get("total", 0),
                "created":        data.get("created", 0),
                "failed":         data.get("failed", 0),
                "elapsed_seconds": data.get("elapsed_seconds", 0),
                "timestamp":      path.stat().st_mtime,
                "records":        data.get("records", []),
            })
        except Exception:
            continue
    return rows


@app.get("/api/batch-create/{run_id}/export")
def batch_export_endpoint(run_id: str):
    """Download Excel file of batch creation results."""
    xlsx_path = export_batch_excel(run_id)
    if xlsx_path is None:
        raise HTTPException(status_code=404, detail=f"Batch results not found for run_id: {run_id}")
    from api.batch_create import RESULTS_DIR
    import json
    summary_path = RESULTS_DIR / f"{run_id}.json"
    module = "unknown"
    submodule = "unknown"
    try:
        with open(summary_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        module = data.get("module", "unknown")
        submodule = data.get("sub_module", "unknown")
    except Exception:
        pass
    return FileResponse(
        xlsx_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=f"RhythmERP_Batch_{module}_{submodule}_{run_id}.xlsx",
    )


# ================================================================
# PURCHASE CHAIN ENDPOINT
# ================================================================

@app.post("/api/purchase-chain")
def purchase_chain_endpoint(request: PurchaseChainRequest):
    """Create linked PO->GP->GRN->QC chain(s) via the ERP API (SSE-streamed)."""
    request.count = max(1, min(request.count, 50))
    return StreamingResponse(
        purchase_chain_stream(request),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


# ================================================================
# PB LIST ENDPOINT
# ================================================================

@app.post("/api/pb-list")
def pb_list_endpoint(request: PBListRequest):
    """Fetch recent Purchase Bookings for the given tenant (up to `pages` x 50 records)."""
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    from common.erp_api_client import RhythmERPAPIClient

    token = request.erp_token.replace("Bearer ", "").strip()
    client = RhythmERPAPIClient(tenant_id=request.erp_tenant_id)
    client.login_from_browser(token=token, tenant_id=request.erp_tenant_id)

    results = []
    for page in range(1, 3):
        resp = client.session.get(
            f"{client.BASE_URL}/procure_to_pay/purchase-booking/",
            params={"page": page, "limit": 50, "filters": "", "screen_name": "Purchase Booking", "search": ""},
            timeout=30,
        )
        if resp.status_code != 200:
            break
        data = resp.json()
        rows = data.get("screenmatlistingdata_set") or []
        for r in rows:
            ref = r.get("transaction_ref_no") or ""
            if not ref:
                continue
            results.append({
                "id": r.get("id") or r.get("pk") or "",
                "ref_no": ref,
                "date": r.get("transaction_date") or "",
                "supplier": r.get("supplier_ref_id") or "",
                "amount": r.get("txn_currency_total_amount") or "",
                "taxable_amount": r.get("txn_currency_amount_detail") or "",
                "igst_amount": r.get("txn_currency_igst_amount") or "",
                "cgst_amount": r.get("txn_currency_cgst_amount") or "",
                "sgst_amount": r.get("txn_currency_sgst_amount") or "",
                "gst_type": r.get("gst_type") or "",
                "division": r.get("parameter1") or "",
                "department": r.get("parameter2") or "",
                "type_of_sale": r.get("parameter5") or "",
                "location": r.get("parameter6") or "",
            })
        if not data.get("page_has_next"):
            break

    return JSONResponse({"pbs": results})


# ================================================================
# PB ITEMS ENDPOINT
# ================================================================

class PBItemsRequest(BaseModel):
    erp_token: str
    erp_tenant_id: str
    pb_id: str  # numeric PB id from the listing

@app.post("/api/pb-items")
def pb_items_endpoint(request: PBItemsRequest):
    """Fetch PB detail lines and resolve item names from item master."""
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    from common.erp_api_client import RhythmERPAPIClient

    token = request.erp_token
    if token.startswith("Bearer "):
        token = token[7:]

    client = RhythmERPAPIClient(tenant_id=request.erp_tenant_id)
    client.login_from_browser(token=token, tenant_id=request.erp_tenant_id)

    # Fetch PB detail
    pb_resp = client.session.get(
        f"{client.BASE_URL}/procure_to_pay/purchase-booking/{request.pb_id}/",
        timeout=30,
    )
    if pb_resp.status_code != 200:
        return JSONResponse({"items": [], "error": f"PB detail fetch failed: {pb_resp.status_code}"})

    pb_data = pb_resp.json()
    details = pb_data.get("purchase_booking_details") or []

    # Collect unique item_ref_ids
    item_ids = set(d["item_ref_id"] for d in details if d.get("item_ref_id"))

    # Resolve names via Item Master detail endpoint
    item_names: dict[int, str] = {}
    for iid in item_ids:
        try:
            r = client.session.get(
                f"{client.BASE_URL}/core/dynamic-screen-wrapper/Item%20Master/{iid}/",
                timeout=15,
            )
            if r.status_code == 200:
                item_names[iid] = r.json().get("name") or str(iid)
        except Exception:
            pass

    items = []
    total_igst = total_cgst = total_sgst = 0.0
    for d in details:
        iid = d.get("item_ref_id")
        # Try name from item master lookup, then from inline display fields in PB detail
        name = (
            item_names.get(iid)
            or d.get("item_ref_id_display")
            or d.get("item_name")
            or d.get("item_display")
            or d.get("name")
            or (str(iid) if iid else "—")
        )
        igst = float(d.get("txn_currency_igst_amount") or 0)
        cgst = float(d.get("txn_currency_cgst_amount") or 0)
        sgst = float(d.get("txn_currency_sgst_amount") or 0)
        gst_type = d.get("gst_type") or ""
        items.append({
            "item_ref_id": iid,
            "name": name,
            "quantity": d.get("net_quantity") or d.get("quantity") or "",
            "rate": d.get("rate") or "",
            "amount": d.get("total_amount") or d.get("amount") or "",
            "igst_amount": round(igst, 3) if igst else None,
            "cgst_amount": round(cgst, 3) if cgst else None,
            "sgst_amount": round(sgst, 3) if sgst else None,
            "gst_type": gst_type,
        })

    return JSONResponse({"items": items})


# ================================================================
# JV VERIFY ENDPOINT
# ================================================================

@app.post("/api/jv-verify")
def jv_verify_endpoint(request: JVVerifyRequest):
    """Verify a Purchase Booking's Journal Voucher entry and return structured step results."""
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    from pages.private_b2b.modules.journal_voucher.utils.api_jv_utils import JVAPIUtils
    from common.erp_api_client import RhythmERPAPIClient

    token = request.erp_token
    if token.startswith("Bearer "):
        token = token[7:]

    import concurrent.futures
    client = RhythmERPAPIClient(tenant_id=request.erp_tenant_id)
    client.login_from_browser(token=token, tenant_id=request.erp_tenant_id)
    jv = JVAPIUtils(client)
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            future = ex.submit(jv.verify_pb, request.pb_ref_no, None, None, None, None)
            result = future.result(timeout=38)
    except concurrent.futures.TimeoutError:
        return {
            "steps": [{"n": 1, "label": "Fetch JV report", "ok": False, "detail": "JV report scan timed out — entry not found within 38s"}],
            "account_rows": [],
            "accounting_def": [],
        }
    except Exception as exc:
        return {
            "steps": [{"n": 1, "label": "Fetch JV report", "ok": False, "detail": str(exc)}],
            "account_rows": [],
            "accounting_def": [],
        }

    steps = []
    if result.error:
        steps.append({"n": 1, "label": "Fetch JV report", "ok": False, "detail": result.error})
    elif not result.found:
        steps.append({
            "n": 1, "label": "Fetch JV report", "ok": False,
            "detail": f"{request.pb_ref_no} — not found in JV report",
        })
    else:
        steps.append({"n": 1, "label": "Found in JV report", "ok": True, "detail": request.pb_ref_no})
        steps.append({
            "n": 2, "label": "Accounting fields", "ok": True,
            "fields": [
                {"field": "Division",     "value": result.division    or "—"},
                {"field": "Department",   "value": result.department  or "—"},
                {"field": "Type of Sale", "value": result.type_of_sale or "—"},
                {"field": "Location",     "value": result.location    or "—"},
                {"field": "Commodity",    "value": result.commodity   or "—"},
            ],
        })
        steps.append({
            "n": 3, "label": "Balance check", "ok": result.balanced,
            "detail": f"DR = {result.debit:,.2f}   |CR| = {abs(result.credit):,.2f}",
        })

    # Collect JV account rows — one per child row, with commodity + amount
    account_rows = []
    if result.found:
        for row in result.child_rows:
            name = row.get("account_name") or ""
            dc = row.get("debit_credit_type") or row.get("dr_cr") or ""
            commodity = row.get("commodity") or ""
            if dc == "Debit":
                amount = (row.get("transaction_debit_amount") or row.get("debit_amount")
                          or row.get("base_debit_amount") or row.get("transaction_amount") or "")
            else:
                amount = (row.get("transaction_credit_amount") or row.get("credit_amount")
                          or row.get("base_credit_amount") or row.get("transaction_amount") or "")
            if name:
                account_rows.append({
                    "account_name": name,
                    "dr_cr": dc,
                    "commodity": commodity,
                    "amount": float(amount) if amount else None,
                })

    return JSONResponse({"steps": steps, "ok": result.ok(), "account_rows": account_rows})


# ================================================================
# ACCOUNTING DEFINITION ENDPOINT
# ================================================================

class AccountingDefRequest(BaseModel):
    erp_token: str
    erp_tenant_id: str
    transaction_type_id: str = "5"  # default: Purchase Booking

@app.post("/api/accounting-def")
def accounting_def_endpoint(request: AccountingDefRequest):
    """Fetch accounting definition for a transaction type and resolve account names."""
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    from common.erp_api_client import RhythmERPAPIClient

    token = request.erp_token
    if token.startswith("Bearer "):
        token = token[7:]

    client = RhythmERPAPIClient(tenant_id=request.erp_tenant_id)
    client.login_from_browser(token=token, tenant_id=request.erp_tenant_id)

    # Fetch all accounting definitions
    resp = client.session.get(
        f"{client.BASE_URL}/core/accounting-definition/?page_number=1&page_size=100",
        timeout=30,
    )
    if resp.status_code != 200:
        return JSONResponse({"error": f"accounting-definition fetch failed: {resp.status_code}"}, status_code=500)

    definitions = resp.json()
    target = next((d for d in definitions if str(d.get("transaction_type")) == str(request.transaction_type_id)), None)
    if not target:
        return JSONResponse({"error": f"No accounting definition found for transaction_type={request.transaction_type_id}"}, status_code=404)

    # Operator ID → label
    OPERATOR_LABELS: dict[int, str] = {
        1704: "IN", 1705: "NOT IN", 1970: "IS", 1710: "AND", 1711: "OR",
    }

    from urllib.parse import quote as url_quote

    # Fetch per-parameter detail (parameter_name + field_data_type) for all condition params
    param_detail_cache: dict[int, dict] = {}
    option_master_cache: dict[str, dict[str, str]] = {}  # screen_name → {id_str: name}

    def _param_detail(pid: int) -> dict:
        if pid in param_detail_cache:
            return param_detail_cache[pid]
        try:
            r = client.session.get(
                f"{client.BASE_URL}/core/dynamic-screen-wrapper/Accounting%20Parameter/{pid}/",
                timeout=10,
            )
            if r.status_code == 200:
                d = r.json()
                info = {
                    "name": d.get("parameter_name") or f"param_{pid}",
                    "field_data_type": d.get("field_data_type") or "text",
                }
                param_detail_cache[pid] = info
                return info
        except Exception:
            pass
        fallback = {"name": f"param_{pid}", "field_data_type": "text"}
        param_detail_cache[pid] = fallback
        return fallback

    def _resolve_options(param_name: str, field_data_type: str, options: list) -> list[str]:
        if not options or field_data_type != "dropdown":
            return [str(o) for o in options]

        # Check whether any option looks like an integer ID
        has_int = any(str(o).strip().lstrip('-').isdigit() for o in options)
        if not has_int:
            return [str(o) for o in options]

        # Fetch master listing for this screen (cached)
        if param_name not in option_master_cache:
            id_map: dict[str, str] = {}
            try:
                r = client.session.get(
                    f"{client.BASE_URL}/core/dynamic-screen-wrapper/{url_quote(param_name)}/?page_number=1&page_size=500",
                    timeout=15,
                )
                if r.status_code == 200:
                    rows = r.json().get("screenmatlistingdata_set") or r.json().get("results") or []
                    id_map = {str(row["id"]): row.get("name", str(row["id"])) for row in rows if row.get("id")}
            except Exception:
                pass
            option_master_cache[param_name] = id_map

        id_map = option_master_cache[param_name]
        # Resolve each option individually — integers get looked up, strings kept as-is
        # If not in bulk map, fall back to individual detail fetch
        result = []
        for o in options:
            s = str(o).strip()
            if s.lstrip('-').isdigit():
                name = id_map.get(s)
                if name is None:
                    try:
                        r2 = client.session.get(
                            f"{client.BASE_URL}/core/dynamic-screen-wrapper/{url_quote(param_name)}/{s}/",
                            timeout=5,
                        )
                        if r2.status_code == 200:
                            name = r2.json().get("name") or s
                            id_map[s] = name  # cache for next time
                    except Exception:
                        pass
                result.append(name if name is not None else f"#{s}")
            else:
                result.append(s)
        return result

    def build_condition_text(conditions: list) -> str:
        if not conditions:
            return ""
        parts: list[str] = []
        for i, c in enumerate(conditions):
            pid = int(c.get("parameter") or 0)
            detail = _param_detail(pid)
            param_name = detail["name"]
            op = OPERATOR_LABELS.get(int(c.get("operator") or 0), str(c.get("operator")))
            options = c.get("options") or []
            resolved = _resolve_options(param_name, detail["field_data_type"], options)
            options_str = ", ".join(resolved)
            parts.append(f"{param_name} {op} [{options_str}]")
            if i < len(conditions) - 1 and c.get("logical_operator"):
                log_op = OPERATOR_LABELS.get(int(c.get("logical_operator") or 0), "AND")
                parts.append(log_op)
        return " ".join(parts)

    # Resolve account_ref_id → account name
    account_cache: dict[int, str] = {}
    def resolve_account(ref_id: int) -> str:
        if ref_id in account_cache:
            return account_cache[ref_id]
        try:
            r = client.session.get(
                f"{client.BASE_URL}/core/dynamic-screen-wrapper/Chart%20Of%20Account%20Definition/{ref_id}/",
                timeout=15,
            )
            name = r.json().get("name") or str(ref_id) if r.status_code == 200 else str(ref_id)
        except Exception:
            name = str(ref_id)
        account_cache[ref_id] = name
        return name

    details = []
    for d in target.get("accounting_definition_detail") or []:
        ref_id = d.get("account_ref_id")
        conditions = d.get("conditions") or []
        details.append({
            "id": d.get("id"),
            "account_ref_id": ref_id,
            "account_name": resolve_account(ref_id) if ref_id else "—",
            "dr_cr": d.get("dr_cr"),
            "has_conditions": len(conditions) > 0,
            "condition_text": build_condition_text(conditions),
        })

    return JSONResponse({
        "id": target.get("id"),
        "name": target.get("name"),
        "transaction_type_id": request.transaction_type_id,
        "details": details,
    })


# ================================================================
# TEST CASES ENDPOINT
# ================================================================

TEST_CASES_PATH = PROJECT_ROOT / "api" / "test_cases.json"


@app.get("/api/test-cases")
async def get_test_cases(module: str = None):
    """Return all test cases, optionally filtered by module key."""
    if not TEST_CASES_PATH.exists():
        return JSONResponse({"error": "test_cases.json not found"}, status_code=404)

    try:
        with open(TEST_CASES_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        return JSONResponse({"error": "Invalid JSON in test_cases.json"}, status_code=500)

    if module:
        key = module.lower().replace(" ", "_").replace("-", "_")
        if key in data:
            return {key: data[key]}
        return {"error": f"Module '{module}' not found", "available_modules": list(data.keys())}

    return data


# ================================================================
# MASTER DATA ENDPOINT
# ================================================================

class MasterDataRequest(BaseModel):
    screen: str
    erp_token: str
    erp_tenant_id: str = "681"


def _resolve_tax_rates(client) -> dict:
    """Return ``{hsn_str: [float tax_rates]}`` from the Tax Rate screen.

    Header-level entry details carry flat ``details[]`` rows with
    ``hsn_sac_number`` + ``tax_rate``. Fetched per-header (threaded) so a
    tenant with many rate headers stays fast. Missing/unparseable rates are
    skipped.
    """
    from concurrent.futures import ThreadPoolExecutor

    try:
        resp = client.list_entries("Tax Rate", page_size=500)
    except Exception:
        return {}
    headers = resp.get("screenmatlistingdata_set") or resp.get("results") or []

    def _fetch(header):
        out = {}
        hid = header.get("id")
        if hid is None:
            return out
        try:
            det = client.get_entry("Tax Rate", hid)
        except Exception:
            return out
        if not det:
            return out
        for child in (det.get("children") or []):
            for row in (child.get("details") or []):
                hsn = row.get("hsn_sac_number")
                rate = row.get("tax_rate")
                if hsn is None or rate is None:
                    continue
                try:
                    out.setdefault(str(hsn).strip(), []).append(float(rate))
                except (TypeError, ValueError):
                    continue
        return out

    result: dict = {}
    with ThreadPoolExecutor(max_workers=8) as ex:
        for hsn_map in ex.map(_fetch, headers):
            for hsn, rates in hsn_map.items():
                result.setdefault(hsn, [])
                result[hsn].extend(rates)
    return result


def _filter_party_by_additional_details(client, screen: str, items: list, required_keys: list) -> list:
    """Keep only parties whose 'Additional Details' stepper has all required_keys set."""
    from concurrent.futures import ThreadPoolExecutor

    def _is_complete(item):
        try:
            detail = client.get_entry(screen, item["id"])
            for child in (detail or {}).get("children") or []:
                if child.get("stepper_name") == "Additional Details":
                    return all(child.get(k) is not None for k in required_keys)
        except Exception:
            pass
        return False

    with ThreadPoolExecutor(max_workers=8) as ex:
        results = list(ex.map(_is_complete, items))
    return [item for item, keep in zip(items, results) if keep]


def _filter_registered_suppliers(client, items: list) -> list:
    return _filter_party_by_additional_details(
        client, "Supplier", items,
        ["gst_registration_status", "payment_terms_ref_id", "delivery_terms_ref_id"],
    )


def _filter_valid_customers(client, items: list) -> list:
    """Keep only customers with all SO-required fields set."""
    from concurrent.futures import ThreadPoolExecutor

    def _is_complete(item):
        try:
            detail = client.get_entry("Customer", item["id"])
            children = (detail or {}).get("children") or []
            has_bill = has_ship = has_terms = False
            for child in children:
                stepper = child.get("stepper_name") or ""
                if "Address" in stepper:
                    for row in child.get("details") or []:
                        addr_type = str(row.get("address_type") or "").strip()
                        if addr_type == "42" and row.get("id"):
                            has_bill = True
                        elif addr_type == "43" and row.get("id"):
                            has_ship = True
                elif "Additional" in stepper:
                    has_terms = all(
                        child.get(k) is not None
                        for k in ("payment_terms_ref_id", "delivery_terms_ref_id", "mode_of_delivery_ref_id")
                    )
            return has_bill and has_ship and has_terms
        except Exception:
            pass
        return False

    with ThreadPoolExecutor(max_workers=8) as ex:
        results = list(ex.map(_is_complete, items))
    return [item for item, keep in zip(items, results) if keep]


def _enrich_item_categories(client, items: list, with_tax_rates: bool = False) -> list:
    """Attach ``item_category`` (and optionally ``tax_rates``) to Item Master rows.

    The Item Master *listing* only returns id/name/code/uom/status — the
    category FK (and HSN) live on the full entry. Fetching every item's detail
    is threaded so it stays fast on larger tenants. Items whose detail cannot
    be fetched are kept as-is (they just won't match a category filter).
    """
    from concurrent.futures import ThreadPoolExecutor

    tax_rates = _resolve_tax_rates(client) if with_tax_rates else {}

    def _fetch(item_row):
        iid = item_row.get("id")
        if iid is None:
            return item_row
        try:
            det = client.get_entry("Item Master", iid)
        except Exception:
            return item_row
        if det is None:
            return item_row
        out = dict(item_row)
        out["item_category"] = det.get("item_category")
        if with_tax_rates:
            hsn = det.get("hsn_sac_code")
            if hsn is not None:
                out["hsn_sac_code"] = hsn
                out["tax_rates"] = tax_rates.get(str(hsn).strip(), [])
        return out

    with ThreadPoolExecutor(max_workers=8) as ex:
        return list(ex.map(_fetch, items))


@app.post("/api/master-data")
def master_data_endpoint(request: MasterDataRequest):
    """List entries from any ERP master-data screen."""
    import sys as _sys
    _sys.path.insert(0, str(PROJECT_ROOT))
    from common.erp_api_client import RhythmERPAPIClient

    client = RhythmERPAPIClient()
    try:
        client.login_from_browser(token=request.erp_token, tenant_id=request.erp_tenant_id)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"ERP auth failed: {e}")

    try:
        result = client.list_entries(request.screen, page_size=500)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"ERP request failed: {e}")

    if result is None:
        raise HTTPException(status_code=502, detail=f"ERP returned no data for '{request.screen}' — check token/tenant")
    items = result.get("screenmatlistingdata_set") or result.get("results") or []
    if request.screen == "Item Master":
        items = _enrich_item_categories(client, items, with_tax_rates=True)
    if request.screen == "Supplier":
        items = _filter_registered_suppliers(client, items)
    if request.screen == "Customer":
        items = _filter_valid_customers(client, items)
    return {"items": items, "total": len(items)}


class ItemCategoriesRequest(BaseModel):
    erp_token: str
    erp_tenant_id: str = "681"


@app.post("/api/item-categories")
def item_categories_endpoint(request: ItemCategoriesRequest):
    """List Item Categories with live item counts, sorted by count descending.

    The ERP PO screen filters the Item dropdown by the selected Item Category,
    so the chain must pick items inside one category. This returns every
    category plus how many Item Master entries belong to it, letting the UI
    default to the most-populated category and filter items accordingly.
    """
    import sys as _sys
    _sys.path.insert(0, str(PROJECT_ROOT))
    from common.erp_api_client import RhythmERPAPIClient

    client = RhythmERPAPIClient()
    try:
        client.login_from_browser(token=request.erp_token, tenant_id=request.erp_tenant_id)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"ERP auth failed: {e}")

    def _list(screen: str) -> list:
        try:
            result = client.list_entries(screen, page_size=500)
            return result.get("screenmatlistingdata_set") or result.get("results") or []
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"ERP '{screen}' request failed: {e}")

    cats = _list("Item Category")
    items = _list("Item Master")
    items = _enrich_item_categories(client, items)

    counts: dict = {}
    for it in items:
        cid = it.get("item_category")
        if cid is None:
            continue
        counts[cid] = counts.get(cid, 0) + 1

    out = []
    for c in cats:
        cid = c.get("id")
        if cid is None:
            continue
        out.append({
            "id": int(cid),
            "name": c.get("item_code") or c.get("name") or f"Category {cid}",
            "item_count": int(counts.get(cid, 0)),
        })
    out.sort(key=lambda x: x["item_count"], reverse=True)
    return {"categories": out, "total": len(out)}


class ItemsWithCqpRequest(BaseModel):
    erp_token: str
    erp_tenant_id: str = "681"


@app.post("/api/items-with-cqp")
def items_with_cqp_endpoint(request: ItemsWithCqpRequest):
    """Return the set of Item Master IDs that have a Commodity Quality
    Parameter (CQP) entry configured.

    A QC line references ``item_quality_parameter_ref_id`` per item; when an
    item has no CQP entry the ERP 500s on QC creation. The Purchase Chain UI
    uses this list to show only items that can survive a QC step.
    """
    import sys as _sys
    _sys.path.insert(0, str(PROJECT_ROOT))
    from common.erp_api_client import RhythmERPAPIClient
    from pages.commodity_settings.modules.commodity_quality_parameter.data.commodity_quality_parameter_data import (
        cqp_entry_is_active,
        cqp_transaction_type_is,
        resolve_purchase_transaction_type_id,
    )

    client = RhythmERPAPIClient()
    try:
        client.login_from_browser(token=request.erp_token, tenant_id=request.erp_tenant_id)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"ERP auth failed: {e}")

    try:
        existing = client.list_entries("Commodity Quality Parameter", page_size=500)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"ERP request failed: {e}")

    if existing is None:
        raise HTTPException(status_code=502, detail="ERP returned no data for Commodity Quality Parameter — token may be invalid or expired")

    purchase_id = resolve_purchase_transaction_type_id(client)

    rows = existing.get("screenmatlistingdata_set") or existing.get("results") or []

    # An item is only "usable in QC" when it has a CQP entry with transaction
    # type Purchase AND a from_date strictly BEFORE today. A CQP created today
    # (from_date == today) or with a non-Purchase type (e.g. Spot) is not
    # applied by the QC screen, so it does not count.
    used_ids: set = set()
    for row in rows:
        entry_id = row.get("id")
        if not entry_id:
            continue
        try:
            detail = client.get_entry("Commodity Quality Parameter", entry_id)
        except Exception:
            continue
        if not detail:
            continue
        iid = detail.get("item_ref_id")
        if iid is None:
            continue
        if purchase_id is not None and not cqp_transaction_type_is(detail.get("transaction_type"), purchase_id):
            continue
        if not cqp_entry_is_active(detail.get("from_date")):
            continue
        try:
            used_ids.add(int(iid))
        except (ValueError, TypeError):
            pass

    return {"item_ids": sorted(used_ids), "total": len(used_ids)}


class CqpFillRequest(BaseModel):
    erp_token: str
    erp_tenant_id: str = "681"
    item_ids: list[int] = []


@app.post("/api/cqp-fill")
def cqp_fill_endpoint(request: CqpFillRequest):
    """Create Commodity Quality Parameter (CQP) entries for the given item IDs.

    The Purchase Chain UI calls this when the selected category contains items
    with no CQP entry — without one, the QC step 500s. Reuses the same payload
    builder as the standalone CQP batch script (transaction_type=Purchase,
    1–3 random quality params per item). Entries already present are skipped.
    """
    import sys as _sys
    _sys.path.insert(0, str(PROJECT_ROOT))
    from common.erp_api_client import RhythmERPAPIClient
    from pages.commodity_settings.modules.commodity_quality_parameter.data.commodity_quality_parameter_data import (
        build_cqp_api_payload,
        cqp_entry_is_active,
        resolve_purchase_transaction_type_id,
    )

    client = RhythmERPAPIClient()
    try:
        client.login_from_browser(token=request.erp_token, tenant_id=request.erp_tenant_id)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"ERP auth failed: {e}")

    item_ids = [int(i) for i in request.item_ids if i is not None]
    if not item_ids:
        return {"created": [], "skipped": [], "failed": [], "total": 0}

    # Resolve FK dropdowns: transaction_type (Purchase) + quality params.
    try:
        purchase_id = resolve_purchase_transaction_type_id(client)
        if purchase_id is None:
            client.close()
            raise HTTPException(
                status_code=502,
                detail="Could not resolve 'Purchase' transaction type for CQP — refusing to create with an arbitrary transaction type",
            )
        from common.fk_resolver import FkResolver
        resolver = FkResolver(client)
        qp_map = resolver.resolve("Quality Parameter", parent_screen="Commodity Quality Parameter", field_key="quality_type") or {}
        # Fallbacks if live resolution came up short.
        if not qp_map:
            qp_map = resolver.resolve("Quality Parameter Master") or {}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        client.close()
        raise HTTPException(status_code=502, detail=f"CQP FK resolution failed: {e}")

    if not qp_map:
        client.close()
        raise HTTPException(
            status_code=502,
            detail="Could not resolve CQP FKs (quality_type) for this tenant",
        )

    quality_param_ids = list(qp_map.values())

    def _detail_rows(n: int = 3) -> list:
        import random as _r
        chosen = _r.sample(quality_param_ids, min(n, len(quality_param_ids)))
        return [
            {
                "quality_type": qp_id,
                "min_quality_value": 1,
                "max_quality_value": 100,
                "rate_percentage": False,
                "multiplier": 1,
            }
            for qp_id in chosen
        ]

    # Which items already have a USABLE CQP entry? Only entries whose from_date
    # is strictly before today count — a CQP created today (from_date == today)
    # is not applied by the QC screen until tomorrow. Items with only an
    # inactive entry get a replacement (different to_date) so the unique
    # constraint on (item_ref_id, to_date) is not violated.
    active_items: set = set()
    inactive_items: dict = {}  # item_ref_id -> existing entry's to_date
    try:
        existing = client.list_entries("Commodity Quality Parameter", page_size=500)
        for row in existing.get("screenmatlistingdata_set") or existing.get("results") or []:
            eid = row.get("id")
            if not eid:
                continue
            try:
                det = client.get_entry("Commodity Quality Parameter", eid)
            except Exception:
                continue
            if not det or det.get("item_ref_id") is None:
                continue
            try:
                iid = int(det["item_ref_id"])
            except (ValueError, TypeError):
                continue
            # Only a Purchase CQP can be referenced by the QC step. An entry
            # with any other transaction type (e.g. Spot) is not usable.
            is_purchase = cqp_transaction_type_is(det.get("transaction_type"), purchase_id)
            if is_purchase and cqp_entry_is_active(det.get("from_date")):
                active_items.add(iid)
            elif iid not in inactive_items:
                inactive_items[iid] = det.get("to_date")
    except Exception:
        pass

    created = []
    skipped = []
    failed = []
    for iid in item_ids:
        if iid in active_items:
            skipped.append({"id": iid, "reason": "already has active CQP entry"})
            continue
        # Replacement entry: existing inactive CQP already occupies to_date
        # 2099-12-30T18:30:00Z, so use a different to_date to dodge the
        # (item_ref_id, to_date) unique constraint.
        to_date = "2099-12-31T18:30:00Z" if iid in inactive_items else "2099-12-30T18:30:00Z"
        payload = build_cqp_api_payload(
            item_ref_id=iid,
            transaction_type=purchase_id,
            quality_params=_detail_rows(),
            to_date=to_date,
        )
        try:
            result = client.create_entry(payload)
        except Exception as e:
            failed.append({"id": iid, "reason": str(e)})
            continue
        if result is not None:
            active_items.add(iid)
            created.append({"id": iid, "entry_id": result.get("id")})
        else:
            resp = getattr(client, "_last_raw_response", None)
            body = ""
            if resp is not None:
                try:
                    body = resp.text[:200]
                except Exception:
                    body = "<unreadable>"
            failed.append({"id": iid, "reason": f"HTTP {getattr(resp, 'status_code', '?')}: {body or 'no response'}"})

    try:
        client.close()
    except Exception:
        pass
    return {"created": created, "skipped": skipped, "failed": failed, "total": len(item_ids)}


# ================================================================
# HEALTH ENDPOINT
# ================================================================

@app.get("/api/health")
def health():
    """Health check — no auth required."""
    return {
        "status": "ok",
        "version": "3.0.0",
        "engine": "pure-execution",
        "project_root": str(PROJECT_ROOT),
    }


@app.post("/api/restart")
def restart_server():
    """Dev-only: restart the FastAPI process in-place via os.execv."""
    import threading, os, sys
    def _do_restart():
        import time; time.sleep(0.4)
        os.execv(sys.executable, [sys.executable] + sys.argv)
    threading.Thread(target=_do_restart, daemon=True).start()
    return {"status": "restarting"}


# ================================================================
# CONCURRENCY TESTING ENDPOINTS
# ================================================================

@app.post("/api/concurrency/dispatch")
async def concurrency_dispatch(request: ConcurrencyDispatchRequest):
    """Dispatch a test run to all configured PC agents and merge SSE streams."""
    return StreamingResponse(
        dispatch_concurrent(request),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@app.get("/api/concurrency/agents")
async def concurrency_agents():
    """Ping all configured PC agents and return their health status."""
    return await ping_agents()


# ================================================================
# ENTRY POINT
# ================================================================

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    uvicorn.run(app, host=host, port=port)

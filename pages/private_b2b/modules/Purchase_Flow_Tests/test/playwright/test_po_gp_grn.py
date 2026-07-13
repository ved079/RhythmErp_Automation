"""
Integration tests: Purchase Order → Gate Pass → Goods Receipt Note → QC → PB

TestPOGPGRNFlow               — smoke: PO (all items) → 1 GP → 1 GRN, verifies math.
TestPOSingleItemFullCycle     — sequential E2E: 1-item PO → GP1→GRN1 → GP2→GRN2 → PO Closed.
TestPO_GP_GRN_Single_Item_Flow — parallel E2E: 1-item PO → GP1+GRN1 ‖ GP2+GRN2 → PO Closed.
TestPO_GP_GRN_Multi_Item_Flow  — parallel E2E: 3-item PO → 4 GPs in 2 parallel pairs → PO Closed.
TestPO_GRN_QC_PB_Single_Item_Flow — sequential E2E: 1-item PO → GP → GRN → QC → PB → PO Closed.
TestPO_GRN_QC_PB_Multi_Item_Flow  — sequential E2E: 3-item PO → GP → GRN → QC → PB → PO Closed.

Each class uses an `integration_state` dict (class-scoped) to pass outputs
between sequential test steps.

Parallel worker design
──────────────────────
Each worker thread owns its entire Playwright stack (browser + login) because
Playwright's sync API ties Page objects to the OS thread that created them.
Submit sequencing uses threading.Event pairs so no two GPs or GRNs ever hit
the ERP backend simultaneously — which causes duplicate auto-increment ref numbers.

  gp_done_event  / wait_for_event    — serialises GP submissions
  grn_done_event / wait_for_grn_event — serialises GRN submissions

All form-filling happens in parallel; only the submit clicks are sequenced.
"""

import os
import time
import threading
import traceback
import pytest
from pages.private_b2b.modules.gate_pass.gp_playwright_page import GPPlaywrightPage
from pages.private_b2b.modules.goods_receipt_note.grn_playwright_page import GRNPlaywrightPage
from pages.private_b2b.modules.Purchase_Flow_Tests.excel_exporter import export_pogpgrn_flow

_LOGIN_URL = os.environ.get("RHYTHMERP_LOGIN_URL", "https://rhythmerp.algorhythms.in")
_EMAIL     = os.environ.get("RHYTHMERP_EMAIL", "")
_PASSWORD  = os.environ.get("RHYTHMERP_PASSWORD", "")


@pytest.mark.integration
class TestPOGPGRNFlow:

    # ── Step 1: Purchase Order ───────────────────────────────────────────

    def test_step1_create_po(self, po_page, integration_state):
        """Create a PO with all available items (qty=500 each) and record ref + supplier."""
        t0 = time.time()
        total, row_dicts, supplier_name, location, po_ref_no = po_page.create_record_for_integration(
            all_items=True,
            default_qty=500,
        )
        integration_state.setdefault("_step_times", {})["test_step1_create_po"] = round(time.time() - t0, 1)

        assert po_ref_no, "PO ref_no must be non-empty after creation"
        assert supplier_name, "Supplier name must be captured from PO header"
        assert row_dicts, "PO must have at least one item row"

        integration_state["po_ref_no"]      = po_ref_no
        integration_state["supplier_name"]  = supplier_name
        integration_state["location"]       = location
        integration_state["po_item_rates"]  = {rd["item_name"]: rd["rate"] for rd in row_dicts}

        print(f"\n[PO] ref={po_ref_no}  supplier={supplier_name}  location={location}  items={len(row_dicts)}")

    # ── Step 2: Gate Pass ────────────────────────────────────────────────

    def test_step2_create_gp(self, gp_page, integration_state):
        """Create a GP from the same supplier with 1 item (qty=100) — partial delivery."""
        if not integration_state.get("po_ref_no"):
            pytest.skip("PO was not created in step 1 — skipping GP creation")

        supplier_name = integration_state["supplier_name"]
        t0 = time.time()
        gp_ref_no, gp_rows = gp_page.create_record_with_supplier(
            supplier_name=supplier_name,
            item_configs=[(5, 100)],  # 5 bags, qty=100
            location=integration_state.get("location"),
            type_of_sale="B2B",
        )
        integration_state.setdefault("_step_times", {})["test_step2_create_gp"] = round(time.time() - t0, 1)

        assert gp_ref_no, "GP ref_no must be non-empty after creation"
        assert gp_rows,   "GP must have at least one item row"

        integration_state["gp_ref_no"]   = gp_ref_no
        integration_state["gp_rows"]     = gp_rows
        integration_state["gp_item_name"] = gp_rows[0]["item_name"] if gp_rows else "—"
        integration_state["gp_qty"]       = gp_rows[0]["qty"] if gp_rows else None
        integration_state["gp_bags"]      = 5

        print(f"\n[GP] ref={gp_ref_no}  rows={gp_rows}")

    # ── Step 3: Goods Receipt Note ───────────────────────────────────────

    def test_step3_create_grn_and_verify(self, grn_page, integration_state):
        """Create GRN linking GP→PO and assert auto-filled qty and rate are correct."""
        po_ref_no = integration_state.get("po_ref_no")
        gp_ref_no = integration_state.get("gp_ref_no")
        gp_rows   = integration_state.get("gp_rows", [])
        po_rates  = integration_state.get("po_item_rates", {})

        if not po_ref_no or not gp_ref_no:
            pytest.skip("PO or GP not available from earlier steps")

        grn_page.open_add_form()

        supplier_name = integration_state["supplier_name"]
        grn_page.select_supplier(supplier_name)
        grn_page.select_gate_pass(gp_ref_no)
        grn_page.select_po(po_ref_no)

        # ── Assertions: row count ────────────────────────────────────────
        n_rows = grn_page.count_grn_rows()
        assert n_rows == len(gp_rows), (
            f"GRN should have {len(gp_rows)} row(s) (matching GP), got {n_rows}"
        )

        # ── Collect per-row data for Excel ───────────────────────────────
        grn_gate_pass_qtys = {}
        grn_rates          = {}
        grn_po_remaining   = {}
        total_accepted     = 0

        for i, gp_row in enumerate(gp_rows):
            expected_qty = gp_row["qty"]
            actual_qty   = grn_page.read_gate_pass_qty_nth(i)
            assert abs(actual_qty - expected_qty) < 0.5, (
                f"Row {i}: GRN gate_pass_qty={actual_qty} ≠ GP qty={expected_qty}"
            )

            po_rate  = po_rates.get(gp_row["item_name"], 0)
            grn_rate = grn_page.read_rate_nth(i)
            if po_rate > 0:
                assert abs(grn_rate - po_rate) < 0.01, (
                    f"Row {i} '{gp_row['item_name']}': "
                    f"GRN rate={grn_rate} ≠ PO rate={po_rate}"
                )

            po_remaining = grn_page.read_po_qty_nth(i)
            assert po_remaining >= actual_qty, (
                f"Row {i}: PO remaining={po_remaining} < gate_pass_qty={actual_qty} "
                f"— GRN would be rejected by ERP"
            )

            grn_page.fill_accepted_qty_nth(i, int(expected_qty))

            item = gp_row["item_name"]
            grn_gate_pass_qtys[item] = actual_qty
            grn_rates[item]          = grn_rate
            grn_po_remaining[item]   = po_remaining
            total_accepted          += int(expected_qty)

        # ── Submit ───────────────────────────────────────────────────────
        t0 = time.time()
        grn_ref_no = grn_page.submit()
        integration_state.setdefault("_step_times", {})["test_step3_create_grn_and_verify"] = round(time.time() - t0, 1)

        integration_state["grn_ref_no"]          = grn_ref_no
        integration_state["grn_gate_pass_qtys"]  = grn_gate_pass_qtys
        integration_state["grn_rates"]           = grn_rates
        integration_state["grn_po_remaining"]    = grn_po_remaining
        integration_state["grn_accepted_qty"]    = total_accepted
        integration_state["grn_rate"]            = next(iter(grn_rates.values()), "—")

        assert grn_ref_no, "GRN ref_no must be non-empty after successful submission"
        print(f"\n[GRN] ref={grn_ref_no}")
        print(f"\n[Flow complete] PO={po_ref_no} → GP={gp_ref_no} → GRN={grn_ref_no}")

        # ── Export Excel ─────────────────────────────────────────────────
        step_results = {
            "test_step1_create_po":             {"status": "PASSED", "duration_s": integration_state.get("_step_times", {}).get("test_step1_create_po", "—")},
            "test_step2_create_gp":             {"status": "PASSED", "duration_s": integration_state.get("_step_times", {}).get("test_step2_create_gp", "—")},
            "test_step3_create_grn_and_verify": {"status": "PASSED", "duration_s": integration_state.get("_step_times", {}).get("test_step3_create_grn_and_verify", "—")},
        }
        export_pogpgrn_flow(integration_state, step_results)


# ═══════════════════════════════════════════════════════════════════════════════
# Full E2E cycle — 1 item PO, 2 partial GPs, 2 GRNs → PO closes
# ═══════════════════════════════════════════════════════════════════════════════

PO_QTY   = 200   # total PO quantity for the single item
GP1_QTY  = 120   # first partial delivery
GP2_QTY  = PO_QTY - GP1_QTY   # 80 — remainder, should close the PO


def _create_grn(grn_page, supplier_name, gp_ref_no, po_ref_no,
                expected_gp_qty, expected_po_remaining, expected_rate):
    """Helper: open GRN form, select supplier→GP→PO, assert auto-fill, submit.

    Asserts:
      - gate_pass_qty in GRN == expected_gp_qty
      - po_remaining in GRN == expected_po_remaining
      - rate in GRN == expected_rate (if > 0)
    Returns the new GRN ref_no.
    """
    grn_page.open_add_form()
    grn_page.select_supplier(supplier_name)
    grn_page.select_gate_pass(gp_ref_no)
    grn_page.select_po(po_ref_no)

    n_rows = grn_page.count_grn_rows()
    assert n_rows == 1, f"Expected 1 GRN row, got {n_rows}"

    actual_gp_qty = grn_page.read_gate_pass_qty_nth(0)
    assert abs(actual_gp_qty - expected_gp_qty) < 0.5, (
        f"gate_pass_qty={actual_gp_qty} ≠ expected {expected_gp_qty}"
    )

    actual_po_remaining = grn_page.read_po_qty_nth(0)
    assert abs(actual_po_remaining - expected_po_remaining) < 0.5, (
        f"po_remaining={actual_po_remaining} ≠ expected {expected_po_remaining}"
    )

    if expected_rate > 0:
        actual_rate = grn_page.read_rate_nth(0)
        assert abs(actual_rate - expected_rate) < 0.01, (
            f"GRN rate={actual_rate} ≠ PO rate={expected_rate}"
        )

    grn_page.fill_accepted_qty_nth(0, int(expected_gp_qty))
    return grn_page.submit()


@pytest.mark.integration
class TestPOSingleItemFullCycle:
    """Full E2E: 1-item PO → 2 partial GPs → 2 GRNs → PO balance=0, status=Closed."""

    # ── Step 1: Create PO ────────────────────────────────────────────────

    def test_step1_create_po(self, po_page, integration_state):
        """Create PO with 1 item, qty=200. Capture item_name, rate, supplier, location."""
        total, row_dicts, supplier_name, location, po_ref_no = \
            po_page.create_record_for_integration(
                item_configs=[(PO_QTY, 0, 0)],
            )

        assert po_ref_no,    "PO ref_no must be non-empty"
        assert row_dicts,    "PO must have at least one item row"
        assert supplier_name, "Supplier name must be captured"

        integration_state["po_ref_no"]      = po_ref_no
        integration_state["supplier_name"]  = supplier_name
        integration_state["location"]       = location
        integration_state["item_name"]      = row_dicts[0]["item_name"]
        integration_state["rate"]           = row_dicts[0]["rate"]

        print(
            f"\n[PO] ref={po_ref_no}  item={row_dicts[0]['item_name']}"
            f"  qty={PO_QTY}  rate={row_dicts[0]['rate']}"
            f"  supplier={supplier_name}  location={location}"
        )

    # ── Step 2: First partial GP (qty=120) ──────────────────────────────

    def test_step2_create_gp1(self, gp_page, integration_state):
        """Create GP1 with the same item, qty=120 (partial delivery)."""
        if not integration_state.get("po_ref_no"):
            pytest.skip("PO not created in step 1")

        gp_ref_no, _ = gp_page.create_record_with_specific_item(
            supplier_name=integration_state["supplier_name"],
            item_name=integration_state["item_name"],
            bags=3,
            qty=GP1_QTY,
            location=integration_state["location"],
            type_of_sale="B2B",
        )
        assert gp_ref_no, "GP1 ref_no must be non-empty"
        integration_state["gp1_ref_no"] = gp_ref_no
        print(f"\n[GP1] ref={gp_ref_no}  qty={GP1_QTY}")

    # ── Step 3: GRN1 — assert po_remaining=200, then it drops to 80 ─────

    def test_step3_grn1(self, grn_page, integration_state):
        """GRN1: links GP1→PO. Assert po_remaining=200 (full PO qty still available)."""
        if not integration_state.get("gp1_ref_no"):
            pytest.skip("GP1 not created in step 2")

        grn_ref_no = _create_grn(
            grn_page,
            supplier_name=integration_state["supplier_name"],
            gp_ref_no=integration_state["gp1_ref_no"],
            po_ref_no=integration_state["po_ref_no"],
            expected_gp_qty=GP1_QTY,
            expected_po_remaining=PO_QTY,      # full PO qty — nothing received yet
            expected_rate=integration_state["rate"],
        )
        assert grn_ref_no, "GRN1 ref_no must be non-empty"
        integration_state["grn1_ref_no"] = grn_ref_no
        print(f"\n[GRN1] ref={grn_ref_no}  accepted={GP1_QTY}  po_balance_after={GP2_QTY}")

    # ── Step 4: Second partial GP (qty=80) — runs in Tab 2 ──────────────

    def test_step4_create_gp2(self, gp_page_tab2, integration_state):
        """Create GP2 in Tab 2 (same session). Tab 1 stays on GRN listing untouched."""
        if not integration_state.get("grn1_ref_no"):
            pytest.skip("GRN1 not created in step 3")

        gp_ref_no, _ = gp_page_tab2.create_record_with_specific_item(
            supplier_name=integration_state["supplier_name"],
            item_name=integration_state["item_name"],
            bags=2,
            qty=GP2_QTY,
            location=integration_state["location"],
            type_of_sale="B2B",
        )
        assert gp_ref_no, "GP2 ref_no must be non-empty"
        integration_state["gp2_ref_no"] = gp_ref_no
        print(f"\n[GP2 - Tab2] ref={gp_ref_no}  qty={GP2_QTY}")

    # ── Step 5: GRN2 — runs in Tab 2, asserts po_remaining=80 ───────────

    def test_step5_grn2(self, grn_page_tab2, integration_state):
        """GRN2 in Tab 2. Assert po_remaining=80 (ERP decremented by 120 after GRN1)."""
        if not integration_state.get("gp2_ref_no"):
            pytest.skip("GP2 not created in step 4")

        grn_ref_no = _create_grn(
            grn_page_tab2,
            supplier_name=integration_state["supplier_name"],
            gp_ref_no=integration_state["gp2_ref_no"],
            po_ref_no=integration_state["po_ref_no"],
            expected_gp_qty=GP2_QTY,
            expected_po_remaining=GP2_QTY,     # ERP balance after GRN1 = 200-120 = 80
            expected_rate=integration_state["rate"],
        )
        assert grn_ref_no, "GRN2 ref_no must be non-empty"
        integration_state["grn2_ref_no"] = grn_ref_no
        print(f"\n[GRN2 - Tab2] ref={grn_ref_no}  accepted={GP2_QTY}  po_balance_after=0")

    # ── Step 6: Verify PO is Closed ──────────────────────────────────────

    def test_step6_verify_po_closed(self, po_page, integration_state):
        """After both GRNs, PO balance_qty must be 0 and status must be 'Closed'."""
        po_ref_no = integration_state.get("po_ref_no")
        if not integration_state.get("grn2_ref_no"):
            pytest.skip("GRN2 not submitted in step 5")

        po_page.navigate_to_page()
        # ERP only recalculates PO status when the listing gets a new record.
        # Opening + cancelling the add form triggers that re-fetch.
        po_page.trigger_po_status_recalculation()
        closed = po_page.is_po_closed(po_ref_no)
        assert closed, (
            f"PO {po_ref_no} should be 'Closed' after all quantity received, "
            f"but status column does not show 'Closed'"
        )
        print(
            f"\n[CYCLE COMPLETE]"
            f"\n  PO  = {po_ref_no}  (Closed)"
            f"\n  GP1 = {integration_state['gp1_ref_no']}  qty={GP1_QTY}"
            f"\n  GRN1= {integration_state['grn1_ref_no']}"
            f"\n  GP2 = {integration_state['gp2_ref_no']}  qty={GP2_QTY}"
            f"\n  GRN2= {integration_state['grn2_ref_no']}"
            f"\n  Total received = {PO_QTY}  Balance remaining = 0"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Parallel E2E cycle — GP1+GRN1 and GP2+GRN2 run simultaneously on two tabs
# ═══════════════════════════════════════════════════════════════════════════════

def _login(page, login_url, email, password):
    page.goto(login_url)
    page.wait_for_selector("input[name='Username']", timeout=15000)
    page.fill("input[name='Username']", email)
    page.fill("input[name='Password']", password)
    page.locator("button[type='submit']").click()
    page.wait_for_timeout(1000)
    try:
        page.locator("button[type='submit']").click()
    except Exception:
        pass
    page.wait_for_url(
        lambda url: "signin" not in url.lower() and "authentication" not in url.lower(),
        timeout=20000,
    )


def _gp_grn_worker(login_url, email, password,
                   supplier_name, items, location, po_ref_no,
                   results, errors, key,
                   gp_done_event=None, wait_for_event=None,
                   grn_done_event=None, wait_for_grn_event=None):
    """Universal parallel worker: own Playwright instance → login → GP → GRN.

    items: list of (item_name, bags, qty) — one per GP/GRN row. Works for
    single-item and multi-item GPs identically.

    Submit sequencing via events:
      gp_done_event   — set after GP committed; partner waits on wait_for_event
      grn_done_event  — set after GRN committed; partner waits on wait_for_grn_event
    Both fills happen in parallel; only the submit clicks are serialised.
    """
    from playwright.sync_api import sync_playwright

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False, slow_mo=150)
            page = browser.new_page()
            _login(page, login_url, email, password)

            # Fill GP form (all workers do this simultaneously)
            gp = GPPlaywrightPage(page)
            gp.navigate_to_page()
            gp.fill_items_form(supplier_name, items, location=location, type_of_sale="B2B")

            # Wait for go-ahead before submitting GP
            if wait_for_event is not None:
                wait_for_event.wait()

            gp_ref, row_dicts = gp.submit_items_form(items)
            if gp_done_event is not None:
                gp_done_event.set()

            # Navigate to GRN and open form (both workers do this simultaneously)
            grn = GRNPlaywrightPage(page)
            grn.navigate_to_page()
            grn.open_add_form()
            grn.select_supplier(supplier_name)
            grn.select_gate_pass(gp_ref)
            grn.select_po(po_ref_no)

            # Read gate pass qty per row and fill accepted qty for all rows
            actual_gp_qtys = [grn.read_gate_pass_qty_nth(i) for i in range(len(items))]
            for i, (_, _, qty) in enumerate(items):
                grn.fill_accepted_qty_nth(i, int(qty))

            # Wait for go-ahead before submitting GRN
            if wait_for_grn_event is not None:
                wait_for_grn_event.wait()

            grn_ref = grn.submit()
            if grn_done_event is not None:
                grn_done_event.set()

            browser.close()

        results[key] = {
            "gp_ref":         gp_ref,
            "grn_ref":        grn_ref,
            "items":          row_dicts,
            "actual_gp_qtys": actual_gp_qtys,
        }
    except Exception:
        errors[key] = traceback.format_exc()
        if gp_done_event is not None:
            gp_done_event.set()
        if grn_done_event is not None:
            grn_done_event.set()


@pytest.mark.integration
class TestPO_GP_GRN_Single_Item_Flow:
    """Parallel E2E: 1-item PO → GP1+GRN1 ‖ GP2+GRN2 (two tabs simultaneously) → PO Closed.

    Tab 1 handles the first half of the PO qty, Tab 2 handles the second half — both
    start at the same time. Total wall-clock time ≈ one GP+GRN cycle instead of two.
    """

    # ── Step 1: Create PO (sequential, must complete before parallel split) ──

    def test_step1_create_po(self, po_page, integration_state):
        """Create PO with 1 item, qty=200. Captures item, rate, supplier, location."""
        total, row_dicts, supplier_name, location, po_ref_no = \
            po_page.create_record_for_integration(
                item_configs=[(PO_QTY, 0, 0)],
            )

        assert po_ref_no,     "PO ref_no must be non-empty"
        assert row_dicts,     "PO must have at least one row"
        assert supplier_name, "Supplier must be captured"

        integration_state["po_ref_no"]     = po_ref_no
        integration_state["supplier_name"] = supplier_name
        integration_state["location"]      = location
        integration_state["item_name"]     = row_dicts[0]["item_name"]
        integration_state["rate"]          = row_dicts[0]["rate"]

        print(
            f"\n[PO] ref={po_ref_no}  item={row_dicts[0]['item_name']}"
            f"  qty={PO_QTY}  rate={row_dicts[0]['rate']}"
            f"  supplier={supplier_name}  location={location}"
        )

    # ── Step 2: Parallel GP+GRN on Tab 1 and Tab 2 simultaneously ───────────

    def test_step2_parallel_gp_grn(self, integration_state):
        """GP1+GRN1 and GP2+GRN2 in two browser windows simultaneously.

        Each thread creates its own Playwright instance + browser + login.
        Playwright sync API cannot share Page objects across OS threads (greenlet
        constraint), so each worker owns its entire stack independently.
        Two browser windows open at the same time — wall-clock time ≈ one cycle.
        """
        if not integration_state.get("po_ref_no"):
            pytest.skip("PO not created in step 1")

        supplier  = integration_state["supplier_name"]
        item      = integration_state["item_name"]
        location  = integration_state["location"]
        po_ref_no = integration_state["po_ref_no"]

        items1 = [(item, 3, GP1_QTY)]
        items2 = [(item, 2, GP2_QTY)]

        results = {}
        errors  = {}

        gp1_done  = threading.Event()
        grn1_done = threading.Event()

        t1 = threading.Thread(
            target=_gp_grn_worker,
            args=(_LOGIN_URL, _EMAIL, _PASSWORD,
                  supplier, items1, location, po_ref_no, results, errors, "flow1"),
            kwargs={"gp_done_event": gp1_done, "grn_done_event": grn1_done},
            name="Win1-GP1-GRN1",
        )
        t2 = threading.Thread(
            target=_gp_grn_worker,
            args=(_LOGIN_URL, _EMAIL, _PASSWORD,
                  supplier, items2, location, po_ref_no, results, errors, "flow2"),
            kwargs={"wait_for_event": gp1_done, "wait_for_grn_event": grn1_done},
            name="Win2-GP2-GRN2",
        )

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        if errors:
            msg = "\n\n".join(f"[{k}]\n{v}" for k, v in errors.items())
            pytest.fail(f"Parallel worker(s) failed:\n{msg}")

        for key in ("flow1", "flow2"):
            assert key in results, f"{key} produced no result"
            assert results[key]["grn_ref"], f"{key} GRN ref is empty"
            for i, row in enumerate(results[key]["items"]):
                actual = results[key]["actual_gp_qtys"][i]
                expected = float(row["qty"])
                assert abs(actual - expected) < 0.5, (
                    f"{key} row {i}: gate_pass_qty={actual} ≠ expected {expected}"
                )

        integration_state["parallel_results"] = results
        print(
            f"\n[Win1] GP={results['flow1']['gp_ref']}  GRN={results['flow1']['grn_ref']}  items={results['flow1']['items']}"
            f"\n[Win2] GP={results['flow2']['gp_ref']}  GRN={results['flow2']['grn_ref']}  items={results['flow2']['items']}"
        )

    # ── Step 3: Verify PO is Closed (back on Tab 1) ──────────────────────────

    def test_step3_verify_po_closed(self, po_page, integration_state):
        """Both halves received — PO balance must be 0 and status must be 'Closed'."""
        po_ref_no = integration_state.get("po_ref_no")
        if not integration_state.get("parallel_results"):
            pytest.skip("Parallel step did not complete")

        po_page.navigate_to_page()
        # ERP only recalculates PO status when the listing gets a new record.
        # Opening + cancelling the add form triggers that re-fetch.
        po_page.trigger_po_status_recalculation()
        closed = po_page.is_po_closed(po_ref_no)
        assert closed, (
            f"PO {po_ref_no} should be 'Closed' after all quantity received "
            f"({GP1_QTY} + {GP2_QTY} = {PO_QTY}), but status is not 'Closed'"
        )

        r = integration_state["parallel_results"]
        print(
            f"\n[PARALLEL CYCLE COMPLETE]"
            f"\n  PO   = {po_ref_no}  (Closed ✓)"
            f"\n  Tab1 → GP={r['flow1']['gp_ref']}  GRN={r['flow1']['grn_ref']}  qty={GP1_QTY}"
            f"\n  Tab2 → GP={r['flow2']['gp_ref']}  GRN={r['flow2']['grn_ref']}  qty={GP2_QTY}"
            f"\n  Total received = {PO_QTY}  Balance remaining = 0"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers shared by multi-item parallel tests
# ═══════════════════════════════════════════════════════════════════════════════

def _run_parallel_pair(supplier, location, po_ref_no,
                       items_a, items_b, label_a, label_b):
    """Spin up two worker threads for one parallel GP+GRN pair.

    Flow A fills and submits first (gp_done → grn_done events).
    Flow B fills simultaneously, waits for A's events before each submit.

    Returns results dict keyed by label_a / label_b.
    Raises pytest.fail if either worker errors.
    """
    results = {}
    errors  = {}

    gp_done  = threading.Event()
    grn_done = threading.Event()

    t_a = threading.Thread(
        target=_gp_grn_worker,
        args=(_LOGIN_URL, _EMAIL, _PASSWORD,
              supplier, items_a, location, po_ref_no,
              results, errors, label_a),
        kwargs={"gp_done_event": gp_done, "grn_done_event": grn_done},
        name=f"{label_a}",
    )
    t_b = threading.Thread(
        target=_gp_grn_worker,
        args=(_LOGIN_URL, _EMAIL, _PASSWORD,
              supplier, items_b, location, po_ref_no,
              results, errors, label_b),
        kwargs={"wait_for_event": gp_done, "wait_for_grn_event": grn_done},
        name=f"{label_b}",
    )

    t_a.start()
    t_b.start()
    t_a.join()
    t_b.join()

    if errors:
        msg = "\n\n".join(f"[{k}]\n{v}" for k, v in errors.items())
        pytest.fail(f"Parallel pair [{label_a} ‖ {label_b}] failed:\n{msg}")

    return results


def _assert_pair_results(results, label_a, label_b):
    """Assert both flows in a pair produced valid GP and GRN refs with correct row qtys."""
    for key in (label_a, label_b):
        assert key in results, f"{key} produced no result"
        assert results[key]["gp_ref"],  f"{key} GP ref is empty"
        assert results[key]["grn_ref"], f"{key} GRN ref is empty"
        for i, row in enumerate(results[key]["items"]):
            actual   = results[key]["actual_gp_qtys"][i]
            expected = float(row["qty"])
            assert abs(actual - expected) < 0.5, (
                f"{key} row {i}: gate_pass_qty={actual} ≠ expected {expected}"
            )


def _print_pair(results, label_a, label_b, pair_num):
    for key in (label_a, label_b):
        r = results[key]
        rows = ", ".join(f"{row['item_name']}×{row['qty']}" for row in r["items"])
        print(f"\n  [Pair {pair_num} | {key}]  GP={r['gp_ref']}  GRN={r['grn_ref']}  rows=[{rows}]")


# ═══════════════════════════════════════════════════════════════════════════════
# Multi-item parallel E2E cycle
# ═══════════════════════════════════════════════════════════════════════════════
#
# PO:  A=25  B=20  C=15   (3 items, chosen randomly by the ERP)
#
# Pair 1 (parallel):
#   GP1 → GRN1 :  A=10                (single item, partial A)
#   GP2 → GRN2 :  B=10, C=8          (two items, partial B and C)
#
# Pair 2 (parallel, after both Pair-1 GRNs committed):
#   GP3 → GRN3 :  A=15, B=5          (two items, finishes A, partial B)
#   GP4 → GRN4 :  B=5,  C=7          (two items, finishes B and C)
#
# Totals: A=10+15=25 ✓  B=10+5+5=20 ✓  C=8+7=15 ✓  → PO Closed
#
# Pair 2 waits for Pair 1's threads to join before starting because GP3/GP4
# reference item balances that are only correct after GRN1/GRN2 are committed
# (e.g. GP3 touches A which was partially received in GRN1).
# ═══════════════════════════════════════════════════════════════════════════════

MI_QTY_A = 25   # PO quantity for item A
MI_QTY_B = 20   # PO quantity for item B
MI_QTY_C = 15   # PO quantity for item C


@pytest.mark.integration
class TestPO_GP_GRN_Multi_Item_Flow:
    """Multi-item parallel E2E: 3-item PO → 4 GPs in 2 parallel pairs → PO Closed.

    Pair 1: GP1(A=10) ‖ GP2(B=10,C=8)
    Pair 2: GP3(A=15,B=5) ‖ GP4(B=5,C=7)   ← starts only after Pair 1 GRNs committed

    Validates: single-item GPs, multi-item GPs, partial splits across pairs,
    items shared across different pairs, and final PO closure.
    """

    # ── Step 1: Create PO with 3 items ──────────────────────────────────────

    def test_step1_create_po(self, po_page, integration_state):
        """Create PO with 3 items at fixed qty (A=25, B=20, C=15).

        The ERP picks random item names for A/B/C — we capture them here and
        thread them through all subsequent steps.
        """
        total, row_dicts, supplier_name, location, po_ref_no = \
            po_page.create_record_for_integration(
                item_configs=[
                    (MI_QTY_A, 0, 0),
                    (MI_QTY_B, 0, 0),
                    (MI_QTY_C, 0, 0),
                ],
                forced_location="Pune",
            )

        assert po_ref_no,         "PO ref_no must be non-empty"
        assert len(row_dicts) == 3, f"Expected 3 PO rows, got {len(row_dicts)}"
        assert supplier_name,     "Supplier name must be captured"

        item_a = row_dicts[0]["item_name"]
        item_b = row_dicts[1]["item_name"]
        item_c = row_dicts[2]["item_name"]

        integration_state.update({
            "po_ref_no":    po_ref_no,
            "supplier":     supplier_name,
            "location":     location,
            "item_a":       item_a,
            "item_b":       item_b,
            "item_c":       item_c,
            "rates":        {rd["item_name"]: rd["rate"] for rd in row_dicts},
        })

        print(
            f"\n[PO] ref={po_ref_no}  supplier={supplier_name}  location={location}"
            f"\n  A={item_a} qty={MI_QTY_A}"
            f"\n  B={item_b} qty={MI_QTY_B}"
            f"\n  C={item_c} qty={MI_QTY_C}"
        )

    # ── Step 2: Pair 1 — GP1(A=10) ‖ GP2(B=10,C=8) ─────────────────────────

    def test_step2_pair1_parallel(self, integration_state):
        """Pair 1: GP1→GRN1 (A=10) runs in parallel with GP2→GRN2 (B=10, C=8).

        GP2/GRN2 is multi-row — validates that the worker handles multiple items
        per GP correctly. Pair 2 only starts after this step's threads join.
        """
        if not integration_state.get("po_ref_no"):
            pytest.skip("PO not created in step 1")

        supplier  = integration_state["supplier"]
        location  = integration_state["location"]
        po_ref_no = integration_state["po_ref_no"]
        item_a    = integration_state["item_a"]
        item_b    = integration_state["item_b"]
        item_c    = integration_state["item_c"]

        # GP1: single item — A=10
        items_gp1 = [(item_a, 2, 10)]
        # GP2: two items — B=10, C=8
        items_gp2 = [(item_b, 3, 10), (item_c, 2, 8)]

        results = _run_parallel_pair(
            supplier, location, po_ref_no,
            items_gp1, items_gp2,
            "gp1_grn1", "gp2_grn2",
        )
        _assert_pair_results(results, "gp1_grn1", "gp2_grn2")
        _print_pair(results, "gp1_grn1", "gp2_grn2", pair_num=1)

        integration_state["pair1_results"] = results

    # ── Step 3: Pair 2 — GP3(A=15,B=5) ‖ GP4(B=5,C=7) ─────────────────────

    def test_step3_pair2_parallel(self, integration_state):
        """Pair 2: GP3→GRN3 (A=15,B=5) runs in parallel with GP4→GRN4 (B=5,C=7).

        Both are multi-row GPs. Starts only after Pair 1 threads have joined so
        GRN1/GRN2 are committed and PO balances (A=15, B=10, C=7) are correct.
        """
        if not integration_state.get("pair1_results"):
            pytest.skip("Pair 1 did not complete")

        supplier  = integration_state["supplier"]
        location  = integration_state["location"]
        po_ref_no = integration_state["po_ref_no"]
        item_a    = integration_state["item_a"]
        item_b    = integration_state["item_b"]
        item_c    = integration_state["item_c"]

        # GP3: two items — A=15 (finishes A), B=5 (partial B)
        items_gp3 = [(item_a, 3, 15), (item_b, 1, 5)]
        # GP4: two items — B=5 (finishes B), C=7 (finishes C)
        items_gp4 = [(item_b, 1, 5), (item_c, 2, 7)]

        results = _run_parallel_pair(
            supplier, location, po_ref_no,
            items_gp3, items_gp4,
            "gp3_grn3", "gp4_grn4",
        )
        _assert_pair_results(results, "gp3_grn3", "gp4_grn4")
        _print_pair(results, "gp3_grn3", "gp4_grn4", pair_num=2)

        integration_state["pair2_results"] = results

    # ── Step 4: Verify PO is Closed ──────────────────────────────────────────

    def test_step4_verify_po_closed(self, po_page, integration_state):
        """All 4 GRNs committed — A+B+C fully received — PO must be Closed."""
        po_ref_no = integration_state.get("po_ref_no")
        if not integration_state.get("pair2_results"):
            pytest.skip("Pair 2 did not complete")

        po_page.navigate_to_page()
        po_page.trigger_po_status_recalculation()
        closed = po_page.is_po_closed(po_ref_no)
        assert closed, (
            f"PO {po_ref_no} should be 'Closed' after all items fully received, "
            f"but status is not 'Closed'"
        )

        p1 = integration_state["pair1_results"]
        p2 = integration_state["pair2_results"]
        print(
            f"\n[MULTI-ITEM PARALLEL CYCLE COMPLETE]"
            f"\n  PO = {po_ref_no}  (Closed ✓)"
            f"\n  A={integration_state['item_a']}  total={MI_QTY_A}  splits: 10 + 15"
            f"\n  B={integration_state['item_b']}  total={MI_QTY_B}  splits: 10 + 5 + 5"
            f"\n  C={integration_state['item_c']}  total={MI_QTY_C}  splits: 8 + 7"
            f"\n  Pair 1 → GP={p1['gp1_grn1']['gp_ref']} GRN={p1['gp1_grn1']['grn_ref']}"
            f"         ‖ GP={p1['gp2_grn2']['gp_ref']} GRN={p1['gp2_grn2']['grn_ref']}"
            f"\n  Pair 2 → GP={p2['gp3_grn3']['gp_ref']} GRN={p2['gp3_grn3']['grn_ref']}"
            f"         ‖ GP={p2['gp4_grn4']['gp_ref']} GRN={p2['gp4_grn4']['grn_ref']}"
        )


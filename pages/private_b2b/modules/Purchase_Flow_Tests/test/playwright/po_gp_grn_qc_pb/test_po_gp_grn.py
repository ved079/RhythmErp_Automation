"""
Integration tests: Purchase Order → Gate Pass → Goods Receipt Note → QC → PB

TestPO_GP_GRN_Multi_Item_Flow         — parallel E2E: 3-item PO → 4 GPs in 2 parallel pairs → PO Closed.
TestPO_GRN_QC_PB_Single_Item_Flow     — sequential E2E: 1-item PO → GP1→GRN1→QC1 → GP2→GRN2→QC2 → PB1→PB2.
TestPO_GRN_QC_PB_Multi_Item_Single_GP — sequential E2E: 5-item PO → 1 GP (all items, full qty) → GRN → QC → PB.
TestPO_GRN_QC_PB_Multi_GP             — dynamic parallel E2E: 5-item PO → random 2-5 GPs (random split) → each GP: GRN→QC→PB in parallel.

Each class uses an `integration_state` dict (class-scoped) to pass outputs
between sequential test steps.

Parallel worker design
──────────────────────
Each worker thread owns its entire Playwright stack (browser + login) because
Playwright's sync API ties Page objects to the OS thread that created them.
Submit sequencing uses threading.Event chains so no two GPs, GRNs, QCs, or PBs
ever hit the ERP backend simultaneously.

  gp_events[i]  — worker i waits on events[i-1], sets events[i] after GP submit
  Same chain pattern for grn_events, qc_events, pb_events.

All form-filling happens in parallel; only the submit clicks are sequenced.
"""

import os
import random
import threading
import traceback
import pytest
from pages.private_b2b.modules.gate_pass.gp_playwright_page import GPPlaywrightPage
from pages.private_b2b.modules.goods_receipt_note.grn_playwright_page import GRNPlaywrightPage
from pages.private_b2b.modules.quality_check.qc_playwright_page import QCPlaywrightPage
from conftest import GPPlaywrightPageItemCategory

_LOGIN_URL = "https://rhythmerp.algorhythms.in"
_EMAIL     = "kedar@rhythmflows.com"
_PASSWORD  = "kedar@rhythmflows.com"
_TENANT    = "Agristack Company ltd"


# ═══════════════════════════════════════════════════════════════════════════════
# Full E2E cycle — 1 item PO, 2 partial GPs, 2 GRNs → PO closes (constants)
# ═══════════════════════════════════════════════════════════════════════════════

PO_QTY   = 200   # total PO quantity for the single item
GP1_QTY  = 120   # first partial delivery
GP2_QTY  = PO_QTY - GP1_QTY   # 80 — remainder, should close the PO


def _create_grn(grn_page, supplier_name, gp_ref_no, po_ref_no,
                expected_gp_qty, expected_rate):
    """Helper: open GRN form, select supplier→GP→PO, assert auto-fill, submit.

    Asserts:
      - gate_pass_qty in GRN == expected_gp_qty
      - rate in GRN == expected_rate (if > 0)
    Returns the new GRN ref_no.
    """
    grn_page.open_add_form()
    grn_page.select_supplier(supplier_name)
    grn_page.select_gate_pass(gp_ref_no)
    grn_page.fill_conversion_rate("1")

    n_rows = grn_page.count_grn_rows()
    assert n_rows == 1, f"Expected 1 GRN row, got {n_rows}"

    actual_gp_qty = grn_page.read_gate_pass_qty_nth(0)
    assert abs(actual_gp_qty - expected_gp_qty) < 0.5, (
        f"gate_pass_qty={actual_gp_qty} ≠ expected {expected_gp_qty}"
    )

    if expected_rate > 0:
        actual_rate = grn_page.read_rate_nth(0)
        assert abs(actual_rate - expected_rate) < 0.01, (
            f"GRN rate={actual_rate} ≠ PO rate={expected_rate}"
        )

    grn_page.fill_accepted_qty_nth(0, int(expected_gp_qty))
    return grn_page.submit()


# ═══════════════════════════════════════════════════════════════════════════════
# Parallel E2E cycle — GP1+GRN1 and GP2+GRN2 run simultaneously on two tabs
# ═══════════════════════════════════════════════════════════════════════════════

def _login(page, login_url, email, password, tenant=""):
    page.goto(login_url)
    page.wait_for_selector("input[name='Username']", timeout=15000)
    page.fill("input[name='Username']", email)
    page.fill("input[name='Password']", password)
    page.locator("button[type='submit']").click()
    page.wait_for_timeout(2000)

    if tenant:
        page.wait_for_selector("mat-select[aria-label], mat-select", timeout=15000)
        page.locator("mat-select").first.click(force=True)
        page.wait_for_selector(".dd-search-input", timeout=10000)
        page.locator(".dd-search-input").fill(tenant)
        page.wait_for_timeout(800)
        for opt in page.locator(".mat-mdc-select-panel mat-option span.mdc-list-item__primary-text").all():
            if opt.inner_text().strip() == tenant:
                opt.click(force=True)
                break
        try:
            page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
        except Exception:
            page.keyboard.press("Escape")
            page.wait_for_timeout(300)
        page.wait_for_timeout(300)

    page.locator("button[type='submit']").click(force=True)
    page.wait_for_url(
        lambda url: "signin" not in url.lower() and "authentication" not in url.lower(),
        timeout=20000,
    )


def _gp_grn_worker(login_url, email, password,
                   supplier_name, items, location, po_ref_no,
                   results, errors, key, tenant="",
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
            page = browser.new_page(viewport={"width": 1372, "height": 625})
            _login(page, login_url, email, password, tenant)

            # Fill GP form (all workers do this simultaneously)
            gp = GPPlaywrightPageItemCategory(page)
            gp.navigate_to_page()
            gp.fill_items_form(supplier_name, items, location=location, type_of_sale="B2B", po_ref_no=po_ref_no)

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


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers shared by multi-item parallel tests
# ═══════════════════════════════════════════════════════════════════════════════

def _run_parallel_pair(supplier, location, po_ref_no,
                       items_a, items_b, label_a, label_b, tenant=""):
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
              results, errors, label_a, tenant),
        kwargs={"gp_done_event": gp_done, "grn_done_event": grn_done},
        name=f"{label_a}",
    )
    t_b = threading.Thread(
        target=_gp_grn_worker,
        args=(_LOGIN_URL, _EMAIL, _PASSWORD,
              supplier, items_b, location, po_ref_no,
              results, errors, label_b, tenant),
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
            "gp1_grn1", "gp2_grn2", _TENANT,
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
            "gp3_grn3", "gp4_grn4", _TENANT,
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


# ═══════════════════════════════════════════════════════════════════════════════
# Full E2E with QC — 1 item PO → GP1→GRN1→QC1 → GP2→GRN2→QC2 → PO Closed
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestPO_GRN_QC_PB_Single_Item_Flow:
    """Sequential E2E: 1-item PO → GP1→GRN1→QC1 → GP2→GRN2→QC2 → PO Closed."""

    def test_step1_create_po(self, po_page, integration_state):
        total, row_dicts, supplier_name, location, po_ref_no = \
            po_page.create_record_for_integration(item_configs=[(PO_QTY, 0, 0)])

        assert po_ref_no,     "PO ref_no must be non-empty"
        assert row_dicts,     "PO must have at least one item row"
        assert supplier_name, "Supplier name must be captured"

        integration_state["po_ref_no"]     = po_ref_no
        integration_state["supplier_name"] = supplier_name
        integration_state["location"]      = location
        integration_state["item_name"]     = row_dicts[0]["item_name"]
        integration_state["rate"]          = row_dicts[0]["rate"]
        print(f"\n[PO] ref={po_ref_no}  item={row_dicts[0]['item_name']}  qty={PO_QTY}  supplier={supplier_name}")

    def test_step2_create_gp1(self, gp_page, integration_state):
        if not integration_state.get("po_ref_no"):
            pytest.skip("PO not created in step 1")

        gp_ref_no, _ = gp_page.create_record_with_specific_item(
            supplier_name=integration_state["supplier_name"],
            item_name=integration_state["item_name"],
            bags=3,
            qty=GP1_QTY,
            location=integration_state["location"],
            type_of_sale="B2B",
            po_ref_no=integration_state["po_ref_no"],
        )
        assert gp_ref_no, "GP1 ref_no must be non-empty"
        integration_state["gp1_ref_no"] = gp_ref_no
        print(f"\n[GP1] ref={gp_ref_no}  qty={GP1_QTY}")

    def test_step3_grn1(self, grn_page, integration_state):
        if not integration_state.get("gp1_ref_no"):
            pytest.skip("GP1 not created in step 2")

        grn_ref_no = _create_grn(
            grn_page,
            supplier_name=integration_state["supplier_name"],
            gp_ref_no=integration_state["gp1_ref_no"],
            po_ref_no=integration_state["po_ref_no"],
            expected_gp_qty=GP1_QTY,
            expected_rate=integration_state["rate"],
        )
        assert grn_ref_no, "GRN1 ref_no must be non-empty"
        integration_state["grn1_ref_no"] = grn_ref_no
        print(f"\n[GRN1] ref={grn_ref_no}  accepted={GP1_QTY}")

    def test_step4_qc1(self, qc_page, integration_state):
        if not integration_state.get("grn1_ref_no"):
            pytest.skip("GRN1 not created in step 3")

        qc_ref_no = qc_page.create_for_integration(
            supplier_name=integration_state["supplier_name"],
            gp_ref_no=integration_state["gp1_ref_no"],
            accepted_qty=GP1_QTY,
        )
        assert qc_ref_no, "QC1 ref_no must be non-empty"
        integration_state["qc1_ref_no"] = qc_ref_no
        print(f"\n[QC1] ref={qc_ref_no}  gp={integration_state['gp1_ref_no']}")

    def test_step5_create_gp2(self, gp_page_tab2, integration_state):
        if not integration_state.get("qc1_ref_no"):
            pytest.skip("QC1 not created in step 4")

        gp_ref_no, _ = gp_page_tab2.create_record_with_specific_item(
            supplier_name=integration_state["supplier_name"],
            item_name=integration_state["item_name"],
            bags=2,
            qty=GP2_QTY,
            location=integration_state["location"],
            type_of_sale="B2B",
            po_ref_no=integration_state["po_ref_no"],
        )
        assert gp_ref_no, "GP2 ref_no must be non-empty"
        integration_state["gp2_ref_no"] = gp_ref_no
        print(f"\n[GP2] ref={gp_ref_no}  qty={GP2_QTY}")

    def test_step6_grn2(self, grn_page_tab2, integration_state):
        if not integration_state.get("gp2_ref_no"):
            pytest.skip("GP2 not created in step 5")

        grn_ref_no = _create_grn(
            grn_page_tab2,
            supplier_name=integration_state["supplier_name"],
            gp_ref_no=integration_state["gp2_ref_no"],
            po_ref_no=integration_state["po_ref_no"],
            expected_gp_qty=GP2_QTY,
            expected_rate=integration_state["rate"],
        )
        assert grn_ref_no, "GRN2 ref_no must be non-empty"
        integration_state["grn2_ref_no"] = grn_ref_no
        print(f"\n[GRN2] ref={grn_ref_no}  accepted={GP2_QTY}")

    def test_step7_qc2(self, qc_page, integration_state):
        if not integration_state.get("grn2_ref_no"):
            pytest.skip("GRN2 not created in step 6")

        qc_ref_no = qc_page.create_for_integration(
            supplier_name=integration_state["supplier_name"],
            gp_ref_no=integration_state["gp2_ref_no"],
            accepted_qty=GP2_QTY,
        )
        assert qc_ref_no, "QC2 ref_no must be non-empty"
        integration_state["qc2_ref_no"] = qc_ref_no
        print(f"\n[QC2] ref={qc_ref_no}  gp={integration_state['gp2_ref_no']}")

    def test_step8_create_pb1(self, pb_page, integration_state):
        if not integration_state.get("qc2_ref_no"):
            pytest.skip("QC2 not created in step 7")

        pb_ref_no = pb_page.create_for_integration(
            supplier_name=integration_state["supplier_name"],
            qc_ref_no=integration_state["qc1_ref_no"],
        )
        assert pb_ref_no, "PB1 ref_no must be non-empty"
        integration_state["pb1_ref_no"] = pb_ref_no
        print(f"\n[PB1] ref={pb_ref_no}  qc={integration_state['qc1_ref_no']}")

    def test_step9_create_pb2(self, pb_page, integration_state):
        if not integration_state.get("pb1_ref_no"):
            pytest.skip("PB1 not created in step 8")

        pb_ref_no = pb_page.create_for_integration(
            supplier_name=integration_state["supplier_name"],
            qc_ref_no=integration_state["qc2_ref_no"],
        )
        assert pb_ref_no, "PB2 ref_no must be non-empty"
        integration_state["pb2_ref_no"] = pb_ref_no
        print(f"\n[PB2] ref={pb_ref_no}  qc={integration_state['qc2_ref_no']}")




# ═══════════════════════════════════════════════════════════════════════════════
# Multi-item single-GP QC flow — 5 item PO, one GP covering all items at full
# qty → GRN → QC (fills all rows) → PO Closed
# ═══════════════════════════════════════════════════════════════════════════════

_MI_GP_N_ITEMS  = 5    # number of items in the PO/GP
_MI_GP_ITEM_QTY = 40   # qty per item (5 × 40 = 200 = PO_QTY)
_MI_GP_BAGS     = 3    # bags per item in the GP


@pytest.mark.integration
class TestPO_GRN_QC_PB_Multi_Item_Single_GP:
    """Sequential E2E: 5-item PO → 1 GP (all items, full qty) → GRN → QC → PO Closed."""

    def test_step1_create_po(self, po_page, integration_state):
        item_configs = [(_MI_GP_ITEM_QTY, 0, 0)] * _MI_GP_N_ITEMS
        total, row_dicts, supplier_name, location, po_ref_no = \
            po_page.create_record_for_integration(item_configs=item_configs)

        assert po_ref_no,                              "PO ref_no must be non-empty"
        assert len(row_dicts) == _MI_GP_N_ITEMS,       f"Expected {_MI_GP_N_ITEMS} PO rows, got {len(row_dicts)}"
        assert supplier_name,                          "Supplier name must be captured"

        integration_state["po_ref_no"]     = po_ref_no
        integration_state["supplier_name"] = supplier_name
        integration_state["location"]      = location
        integration_state["item_names"]    = [rd["item_name"] for rd in row_dicts]
        integration_state["rates"]         = {rd["item_name"]: rd["rate"] for rd in row_dicts}

        items_str = ", ".join(f"{rd['item_name']}×{_MI_GP_ITEM_QTY}" for rd in row_dicts)
        print(f"\n[PO] ref={po_ref_no}  supplier={supplier_name}  items=[{items_str}]")

    def test_step2_create_gp(self, gp_page, integration_state):
        if not integration_state.get("po_ref_no"):
            pytest.skip("PO not created in step 1")

        items = [
            (name, _MI_GP_BAGS, _MI_GP_ITEM_QTY)
            for name in integration_state["item_names"]
        ]
        # GPPlaywrightPageItemCategory is defined in the local conftest and supports multi-item forms
        from conftest import GPPlaywrightPageItemCategory
        gp_multi = GPPlaywrightPageItemCategory(gp_page.page)
        gp_multi.fill_items_form(
            supplier_name=integration_state["supplier_name"],
            items=items,
            location=integration_state["location"],
            type_of_sale="B2B",
            po_ref_no=integration_state["po_ref_no"],
        )
        gp_ref_no, row_dicts = gp_multi.submit_items_form(items)
        assert gp_ref_no, "GP ref_no must be non-empty"
        integration_state["gp_ref_no"]  = gp_ref_no
        integration_state["gp_qtys"]    = [_MI_GP_ITEM_QTY] * _MI_GP_N_ITEMS
        print(f"\n[GP] ref={gp_ref_no}  items={_MI_GP_N_ITEMS}  qty_each={_MI_GP_ITEM_QTY}")

    def test_step3_grn(self, grn_page, integration_state):
        if not integration_state.get("gp_ref_no"):
            pytest.skip("GP not created in step 2")

        grn_page.open_add_form()
        grn_page.select_supplier(integration_state["supplier_name"])
        grn_page.select_gate_pass(integration_state["gp_ref_no"])
        grn_page.fill_conversion_rate("1")

        n_rows = grn_page.count_grn_rows()
        assert n_rows == _MI_GP_N_ITEMS, f"Expected {_MI_GP_N_ITEMS} GRN rows, got {n_rows}"

        for i in range(n_rows):
            actual_gp_qty = grn_page.read_gate_pass_qty_nth(i)
            assert abs(actual_gp_qty - _MI_GP_ITEM_QTY) < 0.5, (
                f"Row {i}: gate_pass_qty={actual_gp_qty} ≠ expected {_MI_GP_ITEM_QTY}"
            )
            grn_page.fill_accepted_qty_nth(i, _MI_GP_ITEM_QTY)

        grn_ref_no = grn_page.submit()
        assert grn_ref_no, "GRN ref_no must be non-empty"
        integration_state["grn_ref_no"] = grn_ref_no
        print(f"\n[GRN] ref={grn_ref_no}  rows={n_rows}  accepted_each={_MI_GP_ITEM_QTY}")

    def test_step4_qc(self, qc_page, integration_state):
        if not integration_state.get("grn_ref_no"):
            pytest.skip("GRN not created in step 3")

        accepted_qtys = [_MI_GP_ITEM_QTY] * _MI_GP_N_ITEMS
        qc_ref_no = qc_page.create_for_integration(
            supplier_name=integration_state["supplier_name"],
            gp_ref_no=integration_state["gp_ref_no"],
            accepted_qty=accepted_qtys,
        )
        assert qc_ref_no, "QC ref_no must be non-empty"
        integration_state["qc_ref_no"] = qc_ref_no
        print(f"\n[QC] ref={qc_ref_no}  gp={integration_state['gp_ref_no']}  rows={_MI_GP_N_ITEMS}")

    def test_step5_create_pb(self, pb_page, integration_state):
        if not integration_state.get("qc_ref_no"):
            pytest.skip("QC not created in step 4")

        pb_ref_no = pb_page.create_for_integration(
            supplier_name=integration_state["supplier_name"],
            qc_ref_no=integration_state["qc_ref_no"],
        )
        assert pb_ref_no, "PB ref_no must be non-empty"
        integration_state["pb_ref_no"] = pb_ref_no
        print(f"\n[PB] ref={pb_ref_no}  qc={integration_state['qc_ref_no']}  rows={_MI_GP_N_ITEMS}")


# ═══════════════════════════════════════════════════════════════════════════════
# Dynamic multi-GP flow — 5-item PO, random 2-5 GPs with random item/qty split,
# each GP runs its own GRN→QC→PB chain in parallel.
# ═══════════════════════════════════════════════════════════════════════════════

_MULTI_GP_N_ITEMS     = 5
_MULTI_GP_QTY_RANGE   = (80, 150)   # qty per item in the PO
_MULTI_GP_N_GPS_RANGE = (2, 5)      # how many GPs to split across


def _split_qty(total, n):
    """Split total into n positive integers summing to total."""
    if n == 1:
        return [total]
    parts = [1] * n
    remaining = total - n
    for i in range(n - 1):
        take = random.randint(0, remaining)
        parts[i] += take
        remaining -= take
    parts[-1] += remaining
    return parts


def _generate_gp_splits(item_names, item_qtys, n_gps):
    """Randomly distribute items across n_gps GPs. Every GP gets ≥1 item."""
    gp_items = [[] for _ in range(n_gps)]
    for name, total_qty in zip(item_names, item_qtys):
        n_assigned = random.randint(1, min(n_gps, total_qty))
        assigned   = random.sample(range(n_gps), n_assigned)
        splits     = _split_qty(total_qty, n_assigned)
        for gp_idx, qty in zip(assigned, splits):
            gp_items[gp_idx].append((name, random.randint(1, 5), int(qty)))
    # Guarantee no GP is left empty
    for i, gp in enumerate(gp_items):
        if not gp:
            for other in gp_items:
                if len(other) > 1:
                    gp_items[i].append(other.pop())
                    break
    return gp_items


@pytest.mark.integration
class TestPO_GRN_QC_PB_Multi_GP:
    """Dynamic sequential E2E: 5-item PO → random 2-5 GPs (random item/qty split) → GP→GRN→QC→PB per chain, same window."""

    def test_step1_create_po(self, po_page, integration_state):
        item_configs = [(random.randint(*_MULTI_GP_QTY_RANGE), 0, 0)
                        for _ in range(_MULTI_GP_N_ITEMS)]
        total, row_dicts, supplier_name, location, po_ref_no = \
            po_page.create_record_for_integration(item_configs=item_configs)

        assert po_ref_no,                               "PO ref_no must be non-empty"
        assert len(row_dicts) == _MULTI_GP_N_ITEMS,     f"Expected {_MULTI_GP_N_ITEMS} PO rows, got {len(row_dicts)}"
        assert supplier_name,                           "Supplier name must be captured"

        integration_state["po_ref_no"]     = po_ref_no
        integration_state["supplier_name"] = supplier_name
        integration_state["location"]      = location
        integration_state["item_names"]    = [rd["item_name"] for rd in row_dicts]
        integration_state["item_qtys"]     = [cfg[0] for cfg in item_configs]

        items_str = ", ".join(
            f"{rd['item_name']}×{cfg[0]}"
            for rd, cfg in zip(row_dicts, item_configs)
        )
        print(f"\n[PO] ref={po_ref_no}  supplier={supplier_name}  items=[{items_str}]")

    def test_step2_gp_chains(self, gp_page, grn_page, qc_page, pb_page, integration_state):
        if not integration_state.get("po_ref_no"):
            pytest.skip("PO not created in step 1")

        supplier   = integration_state["supplier_name"]
        location   = integration_state["location"]
        po_ref_no  = integration_state["po_ref_no"]
        item_names = integration_state["item_names"]
        item_qtys  = integration_state["item_qtys"]

        n_gps     = random.randint(*_MULTI_GP_N_GPS_RANGE)
        gp_splits = _generate_gp_splits(item_names, item_qtys, n_gps)

        print(f"\n[Split] {n_gps} GPs:")
        for i, items in enumerate(gp_splits):
            rows = ", ".join(f"{name}×{qty}" for name, _, qty in items)
            print(f"  GP{i+1}: [{rows}]")

        chain_refs = []

        for i, items in enumerate(gp_splits):
            # ── GP ──────────────────────────────────────────────────────────
            gp_multi = GPPlaywrightPageItemCategory(gp_page.page)
            gp_multi.navigate_to_page()
            gp_multi.fill_items_form(supplier, items, location=location,
                                     type_of_sale="B2B", po_ref_no=po_ref_no)
            gp_ref, _ = gp_multi.submit_items_form(items)
            assert gp_ref, f"GP{i+1} ref must be non-empty"
            print(f"\n[GP{i+1}] ref={gp_ref}  items={[(n, q) for n, _, q in items]}")

            # ── GRN ─────────────────────────────────────────────────────────
            qty_by_name = {item[0]: item[2] for item in items}
            grn_page.navigate_to_page()
            grn_page.open_add_form()
            grn_page.select_supplier(supplier)
            grn_page.select_gate_pass(gp_ref)
            grn_page.fill_conversion_rate("1")
            row_names = grn_page.read_row_item_names()
            for j, name in enumerate(row_names):
                grn_page.fill_accepted_qty_nth(j, qty_by_name.get(name, 1))
            grn_ref = grn_page.submit()
            assert grn_ref, f"GRN{i+1} ref must be non-empty"
            print(f"\n[GRN{i+1}] ref={grn_ref}")

            # ── QC ──────────────────────────────────────────────────────────
            # Pass a dict so QC rows are matched by item name, not index
            accepted_qty_map = {item[0]: item[2] for item in items}
            qc_page.navigate_to_page()
            qc_ref = qc_page.create_for_integration(
                supplier_name=supplier,
                gp_ref_no=gp_ref,
                accepted_qty=accepted_qty_map if len(items) > 1 else list(accepted_qty_map.values())[0],
            )
            assert qc_ref, f"QC{i+1} ref must be non-empty"
            print(f"\n[QC{i+1}] ref={qc_ref}")

            # ── PB ──────────────────────────────────────────────────────────
            pb_page.navigate_to_page()
            pb_ref = pb_page.create_for_integration(
                supplier_name=supplier,
                qc_ref_no=qc_ref,
            )
            assert pb_ref, f"PB{i+1} ref must be non-empty"
            print(f"\n[PB{i+1}] ref={pb_ref}")

            chain_refs.append({"gp": gp_ref, "grn": grn_ref, "qc": qc_ref, "pb": pb_ref})

        integration_state["chain_refs"] = chain_refs
        print(f"\n[DONE] {n_gps} chains complete:")
        for i, r in enumerate(chain_refs):
            print(f"  Chain {i+1}: GP={r['gp']} GRN={r['grn']} QC={r['qc']} PB={r['pb']}")

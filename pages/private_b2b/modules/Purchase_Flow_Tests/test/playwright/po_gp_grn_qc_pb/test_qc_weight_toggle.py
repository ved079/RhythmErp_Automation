"""
TestQCWeightToggle — 7-9 item QC with explicit Rate/Weight toggle validation.

Flow: PO (7-9 items) → GP (all items, full qty) → GRN → QC
Even-indexed rows: Weight mode ON  → fills QC Deduction Weight
Odd-indexed rows:  Rate mode OFF   → auto-calc deduction

Run:
    pytest pages/private_b2b/modules/Purchase_Flow_Tests/test/playwright/po_gp_grn_qc_pb/test_qc_weight_toggle.py::TestQCWeightToggle -v -s
"""

import random
import pytest
from pages.private_b2b.modules.goods_receipt_note.grn_playwright_page import GRNPlaywrightPage
from pages.private_b2b.modules.quality_check.qc_playwright_page import QCPlaywrightPage
from pages.private_b2b.modules.purchase_booking.pb_playwright_page import PBPlaywrightPage

_N_ITEMS  = random.randint(7, 9)
_ITEM_QTY = 50
_GP_BAGS  = 2

# Even-indexed rows → Weight mode ON; odd → Rate mode (OFF)
_WEIGHT_MODE_ROWS = [i for i in range(_N_ITEMS) if i % 2 == 0]


@pytest.mark.integration
class TestQCWeightToggle:
    """7-9 item PO → GP → GRN → QC with alternating Weight/Rate toggle per row."""

    # ── Step 1: PO ─────────────────────────────────────────────────────────────

    def test_step1_create_po(self, po_page, integration_state):
        item_configs = [(_ITEM_QTY, 0, 0)] * _N_ITEMS
        total, row_dicts, supplier_name, location, po_ref_no = \
            po_page.create_record_for_integration(item_configs=item_configs)

        assert po_ref_no,                 "PO ref_no must be non-empty"
        assert len(row_dicts) == _N_ITEMS, f"Expected {_N_ITEMS} PO rows, got {len(row_dicts)}"

        integration_state["po_ref_no"]     = po_ref_no
        integration_state["supplier_name"] = supplier_name
        integration_state["location"]      = location
        integration_state["item_names"]    = [rd["item_name"] for rd in row_dicts]

        items_str = ", ".join(f"{rd['item_name']}×{_ITEM_QTY}" for rd in row_dicts)
        print(f"\n[PO] ref={po_ref_no}  supplier={supplier_name}  items=[{items_str}]")

    # ── Step 2: GP ─────────────────────────────────────────────────────────────

    def test_step2_create_gp(self, gp_page, integration_state):
        if not integration_state.get("po_ref_no"):
            pytest.skip("PO not created in step 1")

        from conftest import GPPlaywrightPageItemCategory
        gp = GPPlaywrightPageItemCategory(gp_page.page)

        items = [
            (name, _GP_BAGS, _ITEM_QTY)
            for name in integration_state["item_names"]
        ]
        gp.fill_items_form(
            supplier_name=integration_state["supplier_name"],
            items=items,
            location=integration_state["location"],
            type_of_sale="B2B",
            po_ref_no=integration_state["po_ref_no"],
        )
        gp_ref_no, _ = gp.submit_items_form(items)

        assert gp_ref_no, "GP ref_no must be non-empty"
        integration_state["gp_ref_no"] = gp_ref_no
        print(f"\n[GP] ref={gp_ref_no}  items={items}")

    # ── Step 3: GRN ────────────────────────────────────────────────────────────

    def test_step3_create_grn(self, grn_page, integration_state):
        if not integration_state.get("gp_ref_no"):
            pytest.skip("GP not created in step 2")

        grn_page.open_add_form()
        grn_page.select_supplier(integration_state["supplier_name"])
        grn_page.select_gate_pass(integration_state["gp_ref_no"])
        grn_page.fill_conversion_rate("1")

        n_rows = grn_page.count_grn_rows()
        assert n_rows == _N_ITEMS, f"Expected {_N_ITEMS} GRN rows, got {n_rows}"

        for i in range(n_rows):
            grn_page.fill_accepted_qty_nth(i, _ITEM_QTY)

        grn_ref_no = grn_page.submit()
        assert grn_ref_no, "GRN ref_no must be non-empty"
        integration_state["grn_ref_no"] = grn_ref_no
        print(f"\n[GRN] ref={grn_ref_no}")

    # ── Step 4: QC — row 0 Weight ON, row 1 Rate (OFF) ─────────────────────────

    def test_step4_create_qc(self, logged_in_page, integration_state):
        if not integration_state.get("grn_ref_no"):
            pytest.skip("GRN not created in step 3")

        qc = QCPlaywrightPage(logged_in_page)
        qc.navigate_to_page()

        qc_ref_no, row_data = qc.create_for_integration(
            supplier_name=integration_state["supplier_name"],
            gp_ref_no=integration_state["gp_ref_no"],
            accepted_qty=[_ITEM_QTY] * _N_ITEMS,
            weight_mode_rows=_WEIGHT_MODE_ROWS,
        )

        assert qc_ref_no, "QC ref_no must be non-empty"
        integration_state["qc_ref_no"]   = qc_ref_no
        integration_state["qc_row_data"] = row_data
        print(f"\n[QC] ref={qc_ref_no}  n_items={_N_ITEMS}  weight_rows={_WEIGHT_MODE_ROWS}")
        for i, rd in enumerate(row_data):
            mode = "Weight" if rd["use_weight_mode"] else "Rate"
            print(f"  row {i}: mode={mode}  base_rate={rd['base_rate']}  "
                  f"qc_deduction_amount={rd['qc_deduction_amount']}  "
                  f"transaction_amount={rd['transaction_amount']}")

    # ── Step 5: Open saved QC, re-read fields, re-assert ───────────────────────

    def test_step5_verify_qc_record(self, logged_in_page, integration_state):
        if not integration_state.get("qc_ref_no"):
            pytest.skip("QC not created in step 4")

        qc      = QCPlaywrightPage(logged_in_page)
        ref_no  = integration_state["qc_ref_no"]
        row_data = integration_state["qc_row_data"]

        print(f"\n[VERIFY] Opening QC record {ref_no}...")
        qc.open_qc_record(ref_no)

        for i, rd in enumerate(row_data):
            calc = qc._read_row_calc_fields(nth=i)
            print(f"  [POST-SUBMIT] row {i}: base_rate={calc['base_rate']}  "
                  f"qc_deduction_amount={calc['qc_deduction_amount']}  "
                  f"transaction_amount={calc['transaction_amount']}")

            # QC Deduction Amount must match pre-submit value (server didn't change it)
            assert abs(calc["qc_deduction_amount"] - rd["qc_deduction_amount"]) < 1.0, (
                f"Row {i} QC Deduction Amount changed after save: "
                f"pre={rd['qc_deduction_amount']}, post={calc['qc_deduction_amount']}"
            )
            assert abs(calc["transaction_amount"] - rd["transaction_amount"]) < 1.0, (
                f"Row {i} Transaction Amount changed after save: "
                f"pre={rd['transaction_amount']}, post={calc['transaction_amount']}"
            )

            # Weight-mode formula re-check against saved record
            if rd["use_weight_mode"] and rd["deduction_weight"] is not None:
                expected = round(rd["deduction_weight"] * calc["base_rate"], 2)
                actual   = calc["qc_deduction_amount"]
                assert abs(actual - expected) < 1.0, (
                    f"[POST-SUBMIT] Row {i} QC Deduction Amount: "
                    f"expected {expected} (dw={rd['deduction_weight']} × rate={calc['base_rate']}), "
                    f"got {actual}"
                )
                print(f"  [POST-SUBMIT] row {i} Weight: dw={rd['deduction_weight']} × rate={calc['base_rate']} = {expected} ✓")
            else:
                print(f"  [POST-SUBMIT] row {i} Rate: qc_deduction_amount={calc['qc_deduction_amount']} ✓ (unchanged)")

    # ── Step 6: PB ─────────────────────────────────────────────────────────────

    def test_step6_create_pb(self, logged_in_page, integration_state):
        if not integration_state.get("qc_ref_no"):
            pytest.skip("QC not created in step 4")

        pb = PBPlaywrightPage(logged_in_page)
        pb.navigate_to_page()

        pb_ref_no = pb.create_for_integration(
            supplier_name=integration_state["supplier_name"],
            qc_ref_no=integration_state["qc_ref_no"],
        )

        assert pb_ref_no, "PB ref_no must be non-empty"
        integration_state["pb_ref_no"] = pb_ref_no
        print(f"\n[PB] ref={pb_ref_no}")

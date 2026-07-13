"""
Integration tests: Purchase Order → GP → GRN → QC → PB → PO Closed

TestPO_GRN_QC_PB_Single_Item_Flow — 1-item PO → GP → GRN (linked to PO) → QC → PB → PO Closed
TestPO_GRN_QC_PB_Multi_Item_Flow  — 3-item PO → GP → GRN (linked to PO) → QC (3 rows) → PB (3 rows) → PO Closed
"""

import os
import pytest
from pages.private_b2b.modules.gate_pass.gp_playwright_page import GPPlaywrightPage
from pages.private_b2b.modules.goods_receipt_note.grn_playwright_page import GRNPlaywrightPage
from pages.private_b2b.modules.qc.qc_playwright_page import QCPlaywrightPage
from pages.private_b2b.modules.qc.cqp_playwright_page import CQPPlaywrightPage
from pages.private_b2b.modules.purchase_booking.pb_playwright_page import PBPlaywrightPage

_LOGIN_URL = os.environ.get("RHYTHMERP_LOGIN_URL", "https://rhythmerp.algorhythms.in")
_EMAIL     = os.environ.get("RHYTHMERP_EMAIL", "")
_PASSWORD  = os.environ.get("RHYTHMERP_PASSWORD", "")

PO_GRN_QC_PB_QTY = 100


# ═══════════════════════════════════════════════════════════════════════════════
# PO → GP → GRN → QC → PB single-item flow
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestPO_GRN_QC_PB_Single_Item_Flow:
    """Sequential E2E: 1-item PO → GP → GRN (linked to PO) → QC → PB → PO Closed."""

    def test_step1_create_po(self, po_page, integration_state):
        """Create PO with 1 item, qty=100."""
        total, row_dicts, supplier_name, location, po_ref_no = \
            po_page.create_record_for_integration(
                item_configs=[(PO_GRN_QC_PB_QTY, 0, 0)],
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
            f"  qty={PO_GRN_QC_PB_QTY}  supplier={supplier_name}  location={location}"
        )

    def test_step2_create_gp(self, gp_page, integration_state):
        """Create GP with the same item and full PO qty."""
        if not integration_state.get("po_ref_no"):
            pytest.skip("PO not created in step 1")

        gp_ref_no, _ = gp_page.create_record_with_specific_item(
            supplier_name=integration_state["supplier_name"],
            item_name=integration_state["item_name"],
            bags=3,
            qty=PO_GRN_QC_PB_QTY,
            location=integration_state["location"],
            type_of_sale="B2B",
        )

        assert gp_ref_no, "GP ref_no must be non-empty"
        integration_state["gp_ref_no"] = gp_ref_no
        print(f"\n[GP] ref={gp_ref_no}  qty={PO_GRN_QC_PB_QTY}")

    def test_step3_create_grn(self, grn_page, integration_state):
        """Create GRN: select supplier → GP → PO, accept full qty, submit."""
        if not integration_state.get("gp_ref_no"):
            pytest.skip("GP not created in step 2")

        grn_page.open_add_form()
        grn_page.select_supplier(integration_state["supplier_name"])
        grn_page.select_gate_pass(integration_state["gp_ref_no"])
        grn_page.select_po(integration_state["po_ref_no"])

        grn_page.fill_accepted_qty_nth(0, PO_GRN_QC_PB_QTY)
        grn_ref_no = grn_page.submit()

        assert grn_ref_no, "GRN ref_no must be non-empty"
        integration_state["grn_ref_no"] = grn_ref_no
        integration_state["grn_qty"]    = PO_GRN_QC_PB_QTY
        print(f"\n[GRN] ref={grn_ref_no}  accepted={PO_GRN_QC_PB_QTY}")

    def test_step4_create_qc(self, logged_in_page, integration_state):
        """Create QC: select supplier + last GP → GRN auto-patches, fill actual values."""
        if not integration_state.get("grn_ref_no"):
            pytest.skip("GRN not created in step 3")

        supplier_name = integration_state["supplier_name"]
        item_name     = integration_state["item_name"]

        cqp = CQPPlaywrightPage(logged_in_page)
        cqp_config = cqp.read_configs_for_items([item_name])

        qc = QCPlaywrightPage(logged_in_page)
        qc.cqp_config = cqp_config
        qc.item_names = [item_name]

        qc.navigate_to_page()
        qc.open_add_form()
        qc.select_supplier_and_gp(supplier_name)

        grn_qty = qc.read_accepted_qty(0)
        integration_state["grn_qty"] = int(grn_qty) if grn_qty else integration_state["grn_qty"]

        actual_values = qc.safe_actual_values(0, max_pct=15)
        qc.open_qc_param_popup(0)
        qc.fill_actual_values(actual_values)
        qc.click_done()

        qc.page.locator(qc.SUBMIT_BTN).click()
        qc.handle_success_alert()
        qc.navigate_to_page()

        qc_ref_no = qc.get_ref_no_of_first_row()
        assert qc_ref_no, "QC ref_no must be non-empty"
        integration_state["qc_ref_no"] = qc_ref_no
        print(f"\n[QC] ref={qc_ref_no}  grn_qty={integration_state['grn_qty']}")

    def test_step5_create_pb(self, logged_in_page, integration_state):
        """Create PB: select supplier + last QC → items auto-patch, fill qty details."""
        if not integration_state.get("qc_ref_no"):
            pytest.skip("QC not created in step 4")

        supplier_name = integration_state["supplier_name"]
        grn_qty       = integration_state["grn_qty"]

        pb = PBPlaywrightPage(logged_in_page)
        pb.navigate_to_page()
        pb.open_add_form()
        pb.select_supplier_and_qc(supplier_name)

        pb.open_qty_details_popup(0)
        pb.fill_qty_details(no_of_bags=1, qty=grn_qty)
        pb.click_done()

        pb.page.wait_for_timeout(500)
        pb.page.locator(pb.SUBMIT_BTN).click()
        pb.handle_success_alert()
        pb.navigate_to_page()

        pb_ref_no = pb.get_ref_no_of_first_row()
        assert pb_ref_no, "PB ref_no must be non-empty"
        integration_state["pb_ref_no"] = pb_ref_no
        print(f"\n[PB] ref={pb_ref_no}")

    def test_step6_verify_po_closed(self, po_page, integration_state):
        """Full qty received via GRN → PO must be Closed."""
        if not integration_state.get("pb_ref_no"):
            pytest.skip("PB not created in step 5")

        po_page.navigate_to_page()
        po_page.trigger_po_status_recalculation()
        closed = po_page.is_po_closed(integration_state["po_ref_no"])
        assert closed, (
            f"PO {integration_state['po_ref_no']} should be 'Closed' after full qty received"
        )
        print(
            f"\n[FLOW COMPLETE]"
            f"\n  PO  = {integration_state['po_ref_no']}  (Closed ✓)"
            f"\n  GP  = {integration_state['gp_ref_no']}"
            f"\n  GRN = {integration_state['grn_ref_no']}"
            f"\n  QC  = {integration_state['qc_ref_no']}"
            f"\n  PB  = {integration_state['pb_ref_no']}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# PO → GP → GRN → QC → PB multi-item flow
# ═══════════════════════════════════════════════════════════════════════════════

MI_PB_QTY_A = 25
MI_PB_QTY_B = 20
MI_PB_QTY_C = 15


@pytest.mark.integration
class TestPO_GRN_QC_PB_Multi_Item_Flow:
    """Sequential E2E: 3-item PO → GP → GRN → QC → PB → PO Closed."""

    def test_step1_create_po(self, po_page, integration_state):
        """Create PO with 3 items (A=25, B=20, C=15)."""
        total, row_dicts, supplier_name, location, po_ref_no = \
            po_page.create_record_for_integration(
                item_configs=[
                    (MI_PB_QTY_A, 0, 0),
                    (MI_PB_QTY_B, 0, 0),
                    (MI_PB_QTY_C, 0, 0),
                ],
                forced_location="Pune",
            )

        assert po_ref_no,          "PO ref_no must be non-empty"
        assert len(row_dicts) == 3, f"Expected 3 PO rows, got {len(row_dicts)}"
        assert supplier_name,      "Supplier must be captured"

        item_a = row_dicts[0]["item_name"]
        item_b = row_dicts[1]["item_name"]
        item_c = row_dicts[2]["item_name"]

        integration_state.update({
            "po_ref_no":  po_ref_no,
            "supplier":   supplier_name,
            "location":   location,
            "item_a":     item_a,
            "item_b":     item_b,
            "item_c":     item_c,
            "item_names": [item_a, item_b, item_c],
            "grn_qtys":   [MI_PB_QTY_A, MI_PB_QTY_B, MI_PB_QTY_C],
        })

        print(
            f"\n[PO] ref={po_ref_no}  supplier={supplier_name}  location={location}"
            f"\n  A={item_a} qty={MI_PB_QTY_A}"
            f"\n  B={item_b} qty={MI_PB_QTY_B}"
            f"\n  C={item_c} qty={MI_PB_QTY_C}"
        )

    def test_step2_create_gp(self, logged_in_page, integration_state):
        """Create GP with all 3 items at full PO qty each."""
        if not integration_state.get("po_ref_no"):
            pytest.skip("PO not created in step 1")

        supplier = integration_state["supplier"]
        location = integration_state["location"]
        items = [
            (integration_state["item_a"], 3, MI_PB_QTY_A),
            (integration_state["item_b"], 3, MI_PB_QTY_B),
            (integration_state["item_c"], 2, MI_PB_QTY_C),
        ]

        gp = GPPlaywrightPage(logged_in_page)
        gp.navigate_to_page()
        gp.fill_items_form(supplier, items, location=location, type_of_sale="B2B")
        gp_ref_no, _ = gp.submit_items_form(items)

        assert gp_ref_no, "GP ref_no must be non-empty"
        integration_state["gp_ref_no"] = gp_ref_no
        print(f"\n[GP] ref={gp_ref_no}  items={[integration_state['item_a'], integration_state['item_b'], integration_state['item_c']]}")

    def test_step3_create_grn(self, grn_page, integration_state):
        """Create GRN: select supplier → GP → PO, accept full qty for all 3 rows."""
        if not integration_state.get("gp_ref_no"):
            pytest.skip("GP not created in step 2")

        grn_page.open_add_form()
        grn_page.select_supplier(integration_state["supplier"])
        grn_page.select_gate_pass(integration_state["gp_ref_no"])
        grn_page.select_po(integration_state["po_ref_no"])

        n_rows = grn_page.count_grn_rows()
        assert n_rows == 3, f"Expected 3 GRN rows, got {n_rows}"

        grn_qtys = []
        for i in range(n_rows):
            gp_qty = grn_page.read_gate_pass_qty_nth(i)
            grn_page.fill_accepted_qty_nth(i, int(gp_qty))
            grn_qtys.append(int(gp_qty))

        grn_ref_no = grn_page.submit()

        assert grn_ref_no, "GRN ref_no must be non-empty"
        integration_state["grn_ref_no"] = grn_ref_no
        integration_state["grn_qtys"]   = grn_qtys
        print(f"\n[GRN] ref={grn_ref_no}  grn_qtys={grn_qtys}")

    def test_step4_create_qc(self, logged_in_page, integration_state):
        """Create QC: select supplier + last GP → 3 rows auto-patch, fill actual values per row."""
        if not integration_state.get("grn_ref_no"):
            pytest.skip("GRN not created in step 3")

        supplier   = integration_state["supplier"]
        item_names = integration_state["item_names"]

        cqp = CQPPlaywrightPage(logged_in_page)
        cqp_config = cqp.read_configs_for_items(item_names)

        qc = QCPlaywrightPage(logged_in_page)
        qc.cqp_config = cqp_config
        qc.item_names = item_names

        qc.navigate_to_page()
        qc.open_add_form()
        qc.select_supplier_and_gp(supplier)

        qc_row_count = qc.count_item_rows()
        grn_qtys = []
        for i in range(qc_row_count):
            qty = qc.read_accepted_qty(i)
            grn_qtys.append(int(qty) if qty else integration_state["grn_qtys"][i])
            actual_values = qc.safe_actual_values(i, max_pct=15)
            qc.open_qc_param_popup(i)
            qc.fill_actual_values(actual_values)
            qc.click_done()
            qc.page.wait_for_timeout(800)

        qc.page.locator(qc.SUBMIT_BTN).click()
        qc.handle_success_alert()
        qc.navigate_to_page()

        qc_ref_no = qc.get_ref_no_of_first_row()
        assert qc_ref_no, "QC ref_no must be non-empty"
        integration_state["qc_ref_no"] = qc_ref_no
        integration_state["grn_qtys"]  = grn_qtys
        print(f"\n[QC] ref={qc_ref_no}  grn_qtys={grn_qtys}")

    def test_step5_create_pb(self, logged_in_page, integration_state):
        """Create PB: select supplier + last QC → 3 rows auto-patch, fill qty details per row."""
        if not integration_state.get("qc_ref_no"):
            pytest.skip("QC not created in step 4")

        supplier = integration_state["supplier"]
        grn_qtys = integration_state["grn_qtys"]

        pb = PBPlaywrightPage(logged_in_page)
        pb.navigate_to_page()
        pb.open_add_form()
        pb.select_supplier_and_qc(supplier)

        row_count = pb.count_item_rows()
        for i in range(row_count):
            qty = grn_qtys[i] if i < len(grn_qtys) else 1
            pb.open_qty_details_popup(i)
            pb.fill_qty_details(no_of_bags=1, qty=qty)
            pb.click_done()
            pb.page.wait_for_timeout(500)

        pb.page.wait_for_timeout(500)
        pb.page.locator(pb.SUBMIT_BTN).click()
        pb.handle_success_alert()
        pb.navigate_to_page()

        pb_ref_no = pb.get_ref_no_of_first_row()
        assert pb_ref_no, "PB ref_no must be non-empty"
        integration_state["pb_ref_no"] = pb_ref_no
        print(f"\n[PB] ref={pb_ref_no}")

    def test_step6_verify_po_closed(self, po_page, integration_state):
        """All 3 items fully received → PO must be Closed."""
        if not integration_state.get("pb_ref_no"):
            pytest.skip("PB not created in step 5")

        po_page.navigate_to_page()
        po_page.trigger_po_status_recalculation()
        closed = po_page.is_po_closed(integration_state["po_ref_no"])
        assert closed, (
            f"PO {integration_state['po_ref_no']} should be 'Closed' after all items fully received"
        )
        print(
            f"\n[MULTI-ITEM FLOW COMPLETE]"
            f"\n  PO  = {integration_state['po_ref_no']}  (Closed ✓)"
            f"\n  GP  = {integration_state['gp_ref_no']}"
            f"\n  GRN = {integration_state['grn_ref_no']}"
            f"\n  QC  = {integration_state['qc_ref_no']}"
            f"\n  PB  = {integration_state['pb_ref_no']}"
            f"\n  A={integration_state['item_a']} qty={MI_PB_QTY_A}"
            f"\n  B={integration_state['item_b']} qty={MI_PB_QTY_B}"
            f"\n  C={integration_state['item_c']} qty={MI_PB_QTY_C}"
        )

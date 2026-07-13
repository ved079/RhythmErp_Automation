"""
Integration tests: Gate Pass → GRN → QC → PB  (no PO)

TestGP_GRN_QC_PB_Single_Item_Flow — 1-item GP → GRN (no PO) → QC → PB
TestGP_GRN_QC_PB_Multi_Item_Flow  — 3-item GP → GRN (no PO) → QC (3 rows) → PB (3 rows)

These flows start from GP — no Purchase Order is involved.
GRN is created without selecting a PO (supplier + GP only).
A 5s delay after supplier selection in GRN allows auto-patch before GP dropdown is opened.
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


# ═══════════════════════════════════════════════════════════════════════════════
# GP → GRN → QC → PB single-item flow  (no PO)
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestGP_GRN_QC_PB_Single_Item_Flow:
    """Sequential E2E: GP (1 item) → GRN (no PO) → QC → PB."""

    # ── Step 1: Create GP ────────────────────────────────────────────────────

    def test_step1_create_gp(self, logged_in_page, integration_state):
        """Create GP with 1 random item."""
        gp = GPPlaywrightPage(logged_in_page)
        gp.navigate_to_page()
        gp_ref_no, row_dicts = gp.create_record([(3, 50)])

        supplier_name = logged_in_page.locator("td.cdk-column-supplier_ref_id").first.inner_text().strip()

        assert gp_ref_no,     "GP ref_no must be non-empty"
        assert row_dicts,     "GP must have at least one row"
        assert supplier_name, "Supplier must be readable from listing"

        integration_state["gp_ref_no"]     = gp_ref_no
        integration_state["supplier_name"] = supplier_name
        integration_state["item_name"]     = row_dicts[0]["item_name"]
        integration_state["gp_qty"]        = row_dicts[0]["qty"]

        print(f"\n[GP] ref={gp_ref_no}  supplier={supplier_name}  item={row_dicts[0]['item_name']}  qty={row_dicts[0]['qty']}")

    # ── Step 2: Create GRN (no PO) ───────────────────────────────────────────

    def test_step2_create_grn(self, grn_page, integration_state):
        """Create GRN: select supplier → 5s wait → GP, skip PO, accept full GP qty."""
        if not integration_state.get("gp_ref_no"):
            pytest.skip("GP not created in step 1")

        grn_page.open_add_form()
        grn_page.select_supplier(integration_state["supplier_name"])
        grn_page.page.wait_for_timeout(5000)
        grn_page.select_gate_pass(integration_state["gp_ref_no"])

        gp_qty = grn_page.read_gate_pass_qty_nth(0)
        accepted = int(gp_qty) if gp_qty else integration_state["gp_qty"]
        grn_page.fill_accepted_qty_nth(0, accepted)
        grn_ref_no = grn_page.submit()

        assert grn_ref_no, "GRN ref_no must be non-empty"
        integration_state["grn_ref_no"] = grn_ref_no
        integration_state["grn_qty"]    = accepted
        print(f"\n[GRN] ref={grn_ref_no}  accepted={accepted}")

    # ── Step 3: Create QC ────────────────────────────────────────────────────

    def test_step3_create_qc(self, logged_in_page, integration_state):
        """Create QC: select supplier + last GP → GRN auto-patches, fill actual values."""
        if not integration_state.get("grn_ref_no"):
            pytest.skip("GRN not created in step 2")

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

    # ── Step 4: Create PB ────────────────────────────────────────────────────

    def test_step4_create_pb(self, logged_in_page, integration_state):
        """Create PB: select supplier + last QC → items auto-patch, fill qty details."""
        if not integration_state.get("qc_ref_no"):
            pytest.skip("QC not created in step 3")

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
        print(
            f"\n[FLOW COMPLETE]"
            f"\n  GP  = {integration_state['gp_ref_no']}"
            f"\n  GRN = {integration_state['grn_ref_no']}"
            f"\n  QC  = {integration_state['qc_ref_no']}"
            f"\n  PB  = {pb_ref_no}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# GP → GRN → QC → PB multi-item flow  (no PO)
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestGP_GRN_QC_PB_Multi_Item_Flow:
    """Sequential E2E: GP (3 items) → GRN (no PO) → QC (3 rows) → PB (3 rows)."""

    # ── Step 1: Create GP (3 items) ──────────────────────────────────────────

    def test_step1_create_gp(self, logged_in_page, integration_state):
        """Create GP with 3 random items."""
        gp = GPPlaywrightPage(logged_in_page)
        gp.navigate_to_page()
        gp_ref_no, row_dicts = gp.create_record([
            (3, 25),
            (3, 20),
            (2, 15),
        ])

        supplier_name = logged_in_page.locator("td.cdk-column-supplier_ref_id").first.inner_text().strip()

        assert gp_ref_no,          "GP ref_no must be non-empty"
        assert len(row_dicts) == 3, f"Expected 3 GP rows, got {len(row_dicts)}"
        assert supplier_name,      "Supplier must be readable from listing"

        item_names = [rd["item_name"] for rd in row_dicts]
        gp_qtys    = [rd["qty"] for rd in row_dicts]

        integration_state.update({
            "gp_ref_no":  gp_ref_no,
            "supplier":   supplier_name,
            "item_names": item_names,
            "gp_qtys":    gp_qtys,
        })

        print(
            f"\n[GP] ref={gp_ref_no}  supplier={supplier_name}"
            f"\n  items={item_names}  qtys={gp_qtys}"
        )

    # ── Step 2: Create GRN (3 rows, no PO) ───────────────────────────────────

    def test_step2_create_grn(self, grn_page, integration_state):
        """Create GRN: select supplier → 5s wait → GP, skip PO, accept full GP qty per row."""
        if not integration_state.get("gp_ref_no"):
            pytest.skip("GP not created in step 1")

        grn_page.open_add_form()
        grn_page.select_supplier(integration_state["supplier"])
        grn_page.page.wait_for_timeout(5000)
        grn_page.select_gate_pass(integration_state["gp_ref_no"])

        n_rows = grn_page.count_grn_rows()
        assert n_rows == 3, f"Expected 3 GRN rows, got {n_rows}"

        grn_qtys = []
        for i in range(n_rows):
            gp_qty = grn_page.read_gate_pass_qty_nth(i)
            accepted = int(gp_qty) if gp_qty else integration_state["gp_qtys"][i]
            grn_page.fill_accepted_qty_nth(i, accepted)
            grn_qtys.append(accepted)

        grn_ref_no = grn_page.submit()

        assert grn_ref_no, "GRN ref_no must be non-empty"
        integration_state["grn_ref_no"] = grn_ref_no
        integration_state["grn_qtys"]   = grn_qtys
        print(f"\n[GRN] ref={grn_ref_no}  grn_qtys={grn_qtys}")

    # ── Step 3: Create QC (3 rows) ───────────────────────────────────────────

    def test_step3_create_qc(self, logged_in_page, integration_state):
        """Create QC: select supplier + last GP → 3 rows auto-patch, fill actual values per row."""
        if not integration_state.get("grn_ref_no"):
            pytest.skip("GRN not created in step 2")

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

    # ── Step 4: Create PB (3 rows) ───────────────────────────────────────────

    def test_step4_create_pb(self, logged_in_page, integration_state):
        """Create PB: select supplier + last QC → 3 rows auto-patch, fill qty details per row."""
        if not integration_state.get("qc_ref_no"):
            pytest.skip("QC not created in step 3")

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
        print(
            f"\n[FLOW COMPLETE]"
            f"\n  GP  = {integration_state['gp_ref_no']}"
            f"\n  GRN = {integration_state['grn_ref_no']}"
            f"\n  QC  = {integration_state['qc_ref_no']}"
            f"\n  PB  = {pb_ref_no}"
            f"\n  items={integration_state['item_names']}"
            f"\n  grn_qtys={integration_state['grn_qtys']}"
        )

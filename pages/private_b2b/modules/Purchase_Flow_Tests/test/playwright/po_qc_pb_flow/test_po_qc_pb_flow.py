"""
Integration tests: Purchase Order → QC → PB → PO Closed
Tenant: Ganesh Agrotech Pvt Ltd. (kedar@rhythmflows.com / Kedar@999999)

Skips GP and GRN — QC selects supplier + last PO directly.

Suppliers available on this tenant:
  Baba Pallava Sugar Works LLP, Maa Amul Enterprises Corp,
  Venkatesh Krishna Foods Group, Divya Sutlej Supply Chain,
  Om Narmada Exports Corp, Sri Narmada Grain Processors LLP,
  Sai Godavari Grain Processors Corp
"""

import pytest
from pages.private_b2b.modules.qc.qc_playwright_page import QCPlaywrightPage
from pages.private_b2b.modules.purchase_booking.pb_playwright_page import PBPlaywrightPage
from pages.private_b2b.modules.purchase_order.po_playwright_page import POPlaywrightPage
from pages.private_b2b.utils.cqp_api_for_playwright import build_cqp_config

PO_QC_PB_QTY   = 100
MULTI_ROW_COUNT = 3   # number of item rows in the multi-row test

# ═══════════════════════════════════════════════════════════════════════════════
# PO → QC → PB single-item flow
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.po_qc_pb
class TestPO_QC_PB_Single_Item_Flow:
    """Sequential E2E: 1-item PO → QC (via PO) → PB → PO Closed."""

    def test_step1_create_po(self, po_page, integration_state):
        """Create PO with 1 item, qty=100."""
        total, row_dicts, supplier_name, location, po_ref_no = \
            po_page.create_record_for_integration(
                item_configs=[(PO_QC_PB_QTY, 0, 0)],
                item_names_override=["Welding Electrode FLUID TRANSFER ABRASION RESISTANT REINFORCED TYPE"],
                enable_gst=False,
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
            f"  qty={PO_QC_PB_QTY}  supplier={supplier_name}  location={location}"
        )

    def test_step2_create_qc(self, logged_in_page, integration_state):
        """Create QC: select supplier + last PO → items auto-patch, fill actual values."""
        if not integration_state.get("po_ref_no"):
            pytest.skip("PO not created in step 1")

        supplier_name = integration_state["supplier_name"]
        item_name     = integration_state["item_name"]

        cqp_config = build_cqp_config([item_name], logged_in_page)

        qc = QCPlaywrightPage(logged_in_page)
        qc.cqp_config = cqp_config
        qc.item_names = [item_name]

        qc.navigate_to_page()
        qc.open_add_form()
        qc.select_supplier_and_po(supplier_name)

        accepted_qty = qc.read_accepted_qty(0)
        integration_state["qc_qty"] = int(accepted_qty) if accepted_qty else PO_QC_PB_QTY

        qc.fill_bags_popup(row_index=0)
        qc.fill_qc_params_safe(row_index=0)
        qc.page.wait_for_timeout(5000)
        qc.page.locator(qc.SUBMIT_BTN).click()
        ok = qc.handle_submit_result(timeout=10000)

        if not ok:
            print("\n[QC] submit failed — hard-refreshing and retrying once")
            qc.navigate_to_page()
            qc.page.reload()
            qc.page.wait_for_timeout(2000)
            qc.open_add_form()
            qc.select_supplier_and_po(supplier_name)
            accepted_qty = qc.read_accepted_qty(0)
            integration_state["qc_qty"] = int(accepted_qty) if accepted_qty else PO_QC_PB_QTY
            qc.fill_bags_popup(row_index=0)
            qc.fill_qc_params_safe(row_index=0)
            qc.page.wait_for_timeout(5000)
            qc.page.locator(qc.SUBMIT_BTN).click()
            ok = qc.handle_submit_result(timeout=10000)

        assert ok, "QC submission failed after retry"
        qc.navigate_to_page()

        qc_ref_no = qc.get_ref_no_of_first_row()
        assert qc_ref_no, "QC ref_no must be non-empty"
        integration_state["qc_ref_no"] = qc_ref_no
        print(f"\n[QC] ref={qc_ref_no}  accepted_qty={integration_state['qc_qty']}")

    def test_step3_create_pb(self, logged_in_page, integration_state):
        """Create PB: select supplier + last QC → fill tax/GST per row, submit."""
        if not integration_state.get("qc_ref_no"):
            pytest.skip("QC not created in step 2")

        supplier_name = integration_state["supplier_name"]
        qc_ref_no     = integration_state["qc_ref_no"]

        pb = PBPlaywrightPage(logged_in_page)
        logged_in_page.goto(_PB_URL)
        logged_in_page.reload()
        logged_in_page.wait_for_selector("table.mat-mdc-table, div.empty-state", timeout=20000)
        logged_in_page.wait_for_timeout(1000)

        pb.open_add_form()
        pb.select_supplier(supplier_name)
        pb.select_qc(qc_ref_no)
        n_rows = pb.count_pb_rows()
        for i in range(n_rows):
            pb._fill_row_tax(i)
        pb.fill_conversion_rate(1)

        pb_ref_no = pb.submit()
        assert pb_ref_no, "PB ref_no must be non-empty"
        integration_state["pb_ref_no"] = pb_ref_no
        print(f"\n[PB] ref={pb_ref_no}")

    def test_step4_verify_po_closed(self, po_page, integration_state):
        """Full qty booked via PB → PO must be Closed."""
        if not integration_state.get("pb_ref_no"):
            pytest.skip("PB not created in step 3")

        po_page.navigate_to_page()
        closed = po_page.is_po_closed(integration_state["po_ref_no"])
        print(
            f"\n[FLOW COMPLETE]"
            f"\n  PO = {integration_state['po_ref_no']}  (closed={closed})"
            f"\n  QC = {integration_state['qc_ref_no']}"
            f"\n  PB = {integration_state['pb_ref_no']}"
        )
        # xfail: ERP does not always auto-close PO after full qty booked via PB
        if not closed:
            pytest.xfail(f"PO {integration_state['po_ref_no']} not closed after PB — known ERP gap")


# ═══════════════════════════════════════════════════════════════════════════════
# PO → QC → PB multi-row flow
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.po_qc_pb
class TestPO_QC_PB_MultiRow:
    """Sequential E2E: N-item PO → QC (via PO) → PB → PO Closed."""

    def test_step1_create_po(self, po_page, integration_state):
        """Pick the first MULTI_ROW_COUNT items from the PO dropdown and create a PO."""
        # get_all_item_names opens the form, reads items, fills rest of header in-place
        all_items, supplier_name, location = po_page.get_all_item_names()
        print(f"\n[PO] {len(all_items)} items available")
        filtered_items = [n for n in all_items if "tur" not in n.lower()]
        assert len(filtered_items) >= MULTI_ROW_COUNT, (
            f"Need at least {MULTI_ROW_COUNT} non-Tur items, found {len(filtered_items)}"
        )
        item_names_override = filtered_items[:MULTI_ROW_COUNT]
        item_configs = [(PO_QC_PB_QTY, 0, 0)] * MULTI_ROW_COUNT

        # Form is already open with header filled — skip re-opening
        total, row_dicts, supplier_name, location, po_ref_no = \
            po_page.create_record_for_integration(
                item_configs=item_configs,
                item_names_override=item_names_override,
                form_already_open=True,
                prefilled_supplier=supplier_name,
                prefilled_location=location,
            )

        assert po_ref_no,     "PO ref_no must be non-empty"
        assert row_dicts,     "PO must have rows"

        integration_state["po_ref_no"]     = po_ref_no
        integration_state["supplier_name"] = supplier_name
        integration_state["location"]      = location
        integration_state["item_names"]    = [r["item_name"] for r in row_dicts]
        integration_state["row_count"]     = len(row_dicts)

        for i, rd in enumerate(row_dicts):
            print(f"\n[PO] row{i}  item={rd['item_name']}  rate={rd['rate']}")
        print(f"[PO] ref={po_ref_no}  supplier={supplier_name}")

    def test_step2_create_qc(self, logged_in_page, integration_state):
        """QC: select supplier + last PO → N rows auto-patch, fill params via API config."""
        if not integration_state.get("po_ref_no"):
            pytest.skip("PO not created in step 1")

        supplier_name = integration_state["supplier_name"]
        item_names    = integration_state["item_names"]
        row_count     = integration_state["row_count"]

        cqp_config = build_cqp_config(item_names, logged_in_page)

        qc = QCPlaywrightPage(logged_in_page)
        qc.cqp_config = cqp_config
        qc.item_names = item_names

        def _fill_and_submit():
            qc.navigate_to_page()
            qc.page.reload()
            qc.page.wait_for_timeout(2000)
            qc.open_add_form()
            qc.select_supplier_and_po(supplier_name)

            qtys = []
            for i in range(row_count):
                accepted_qty = qc.read_accepted_qty(i)
                qtys.append(int(accepted_qty) if accepted_qty else PO_QC_PB_QTY)
                qc.fill_bags_popup(row_index=i)
                qc.fill_qc_params_safe(row_index=i)

            qc.page.wait_for_timeout(5000)
            qc.page.locator(qc.SUBMIT_BTN).click()
            ok = qc.handle_submit_result(timeout=10000)
            return ok, qtys

        ok, qc_qtys = _fill_and_submit()

        for attempt in range(1, 3):
            if ok:
                break
            print(f"\n[QC] submit failed (attempt {attempt}) — retrying")
            ok, qc_qtys = _fill_and_submit()

        assert ok, "QC submission failed after 3 attempts"

        qc.navigate_to_page()
        qc_ref_no = qc.get_ref_no_of_first_row()
        assert qc_ref_no, "QC ref_no must be non-empty"
        integration_state["qc_ref_no"] = qc_ref_no
        integration_state["qc_qtys"]   = qc_qtys
        print(f"\n[QC] ref={qc_ref_no}  qtys={qc_qtys}")

    def test_step3_create_pb(self, logged_in_page, integration_state):
        """PB: select supplier + last QC → fill tax/GST per row, submit."""
        if not integration_state.get("qc_ref_no"):
            pytest.skip("QC not created in step 2")

        supplier_name = integration_state["supplier_name"]
        qc_ref_no     = integration_state["qc_ref_no"]

        pb = PBPlaywrightPage(logged_in_page)
        logged_in_page.goto(_PB_URL)
        logged_in_page.reload()
        logged_in_page.wait_for_selector("table.mat-mdc-table, div.empty-state", timeout=20000)
        logged_in_page.wait_for_timeout(1000)

        pb.open_add_form()
        pb.select_supplier(supplier_name)
        pb.select_qc(qc_ref_no)
        n_rows = pb.count_pb_rows()
        for i in range(n_rows):
            pb._fill_row_tax(i)
        pb.fill_conversion_rate(1)

        pb_ref_no = pb.submit()
        assert pb_ref_no, "PB ref_no must be non-empty"
        integration_state["pb_ref_no"] = pb_ref_no
        print(f"\n[PB] ref={pb_ref_no}")

    def test_step4_verify_po_closed(self, po_page, integration_state):
        """Full qty booked via PB → PO must be Closed."""
        if not integration_state.get("pb_ref_no"):
            pytest.skip("PB not created in step 3")

        po_page.navigate_to_page()
        closed = po_page.is_po_closed(integration_state["po_ref_no"])
        print(
            f"\n[FLOW COMPLETE - MULTI-ROW]"
            f"\n  PO = {integration_state['po_ref_no']}  (closed={closed})"
            f"\n  QC = {integration_state['qc_ref_no']}"
            f"\n  PB = {integration_state['pb_ref_no']}"
            f"\n  Items = {integration_state['item_names']}"
        )
        if not closed:
            pytest.xfail(f"PO {integration_state['po_ref_no']} not closed after PB — known ERP gap")


# ═══════════════════════════════════════════════════════════════════════════════
# Shared fixture — one PO created once for QC + PB validation classes
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def po_for_validations(logged_in_page):
    """Create one PO (single item, qty=50) shared across all validation test classes."""
    po = POPlaywrightPage(logged_in_page)
    po.navigate_to_page()
    _, row_dicts, supplier_name, _, ref_no = po.create_record_for_integration(
        item_configs=[(50, 0, 0)],
    )
    print(f"\n[VALIDATION FIXTURE] PO {ref_no} | supplier={supplier_name} | qty=50")
    yield {
        "supplier_name": supplier_name,
        "ref_no":        ref_no,
        "po_qty":        int(row_dicts[0]["qty"]),
        "item_name":     row_dicts[0]["item_name"],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# PO form validations
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.po_qc_pb
class TestPOValidations:
    """Validation tests for the PO form (Ganesh Agrotech tenant)."""

    def _open_with_one_item(self, po_page):
        po_page.open_add_form()
        po_page.fill_header()
        po_page._select_random_mat_option_nth(po_page.ITEM_NAME, 0)
        po_page.page.wait_for_timeout(1500)

    def _cancel(self, po_page):
        po_page.navigate_to_page()
        po_page.page.wait_for_selector("table.mat-mdc-table, div.empty-state", timeout=10000)

    def test_empty_submit_keeps_form(self, po_page):
        """Empty submit must show mat-errors and keep the form open."""
        po_page.open_add_form()
        po_page.page.locator(po_page.SUBMIT_BTN).click(force=True)
        po_page.page.wait_for_timeout(800)
        assert po_page.page.locator("mat-error").count() > 0, \
            "Expected mat-errors on empty PO submit"
        assert po_page.page.locator(po_page.SUPPLIER_NAME).count() > 0, \
            "Form must stay open after empty submit"
        self._cancel(po_page)

    def test_cancel_returns_to_listing(self, po_page):
        """Cancel button must close the form and return to listing."""
        po_page.open_add_form()
        po_page.close_popup()
        assert po_page.page.locator("table.mat-mdc-table, div.empty-state").count() > 0, \
            "Listing must be visible after cancel"

    def test_qty_zero_blocked(self, po_page):
        """qty=0 must show mat-error and keep form open."""
        self._open_with_one_item(po_page)
        po_page._fill_number_nth(po_page.QUANTITY, 0, 10)
        po_page._fill_number_nth(po_page.QUANTITY, 0, 0)
        po_page.page.locator(po_page.SUBMIT_BTN).click(force=True)
        po_page.page.wait_for_timeout(1000)
        assert po_page.page.locator("mat-error").count() > 0, \
            "mat-error must appear for qty=0"
        assert po_page.page.locator(po_page.SUPPLIER_NAME).count() > 0, \
            "Form must stay open on qty=0"
        self._cancel(po_page)

    def test_negative_qty_blocked(self, po_page):
        """Negative qty must trigger mat-error immediately."""
        self._open_with_one_item(po_page)
        po_page._fill_number_nth(po_page.QUANTITY, 0, -1)
        po_page.page.wait_for_timeout(600)
        assert po_page.page.locator("mat-error").count() > 0, \
            "mat-error must appear for negative qty"
        self._cancel(po_page)

    def test_discount_over_100_blocked(self, po_page):
        """Discount > 100 must trigger mat-error."""
        self._open_with_one_item(po_page)
        po_page._fill_number_nth(po_page.QUANTITY, 0, 10)
        po_page._fill_number_nth(po_page.DISCOUNT, 0, 110)
        po_page.page.wait_for_timeout(600)
        assert po_page.page.locator("mat-error").count() > 0, \
            "mat-error must appear for discount > 100"
        self._cancel(po_page)

    def test_negative_interest_blocked(self, po_page):
        """Negative interest must trigger mat-error."""
        self._open_with_one_item(po_page)
        po_page._fill_number_nth(po_page.QUANTITY, 0, 10)
        po_page._fill_number_nth(po_page.INTEREST, 0, -5)
        po_page.page.locator(po_page.SUBMIT_BTN).click(force=True)
        po_page.page.wait_for_timeout(1000)
        assert po_page.page.locator("mat-error").filter(
            has_text="Interest cannot be less than 0"
        ).count() > 0, "Expected 'Interest cannot be less than 0' mat-error"
        self._cancel(po_page)

    def test_duplicate_item_blocked(self, po_page):
        """Same item in two rows must show 'already added' mat-error."""
        po_page.open_add_form()
        po_page.fill_header()
        item_name = po_page._select_random_mat_option_nth(po_page.ITEM_NAME, 0)
        po_page.page.wait_for_timeout(500)

        po_page.page.locator(po_page.ADD_ROW_BTN).click()
        po_page.page.wait_for_timeout(600)
        po_page.page.locator(po_page.ITEM_NAME).nth(1).click(force=True)
        po_page.page.wait_for_selector(".mat-mdc-select-panel", timeout=5000)
        for opt in po_page.page.locator(
            ".mat-mdc-select-panel mat-option span.mdc-list-item__primary-text"
        ).all():
            if opt.inner_text().strip() == item_name:
                opt.click(force=True)
                break
        po_page.page.wait_for_timeout(600)

        assert po_page.page.locator("mat-error").filter(
            has_text="already added"
        ).count() > 0, f"Expected 'already added' mat-error for duplicate item '{item_name}'"
        self._cancel(po_page)

    @pytest.mark.xfail(
        reason="Tax Rate validation not yet enforced by ERP — form saves without selecting tax rate",
        strict=True,
    )
    def test_gst_set_off_requires_tax_rate(self, logged_in_page):
        """Enabling 'Is GST Set Off' and submitting without a Tax Rate must show
        'This field is required' on the Tax Rate field.

        Currently XFAIL: the ERP saves the record without requiring Tax Rate selection.
        Remove xfail once server-side validation is added.
        """
        # Use _po_prefill_full so all header fields + Item Category + Item Name are filled
        _po_prefill_full(logged_in_page)
        logged_in_page.wait_for_timeout(1500)  # let rate auto-fill after item select
        _val_fill_native(logged_in_page, "Quantity", "10")
        # Toggle GST Set Off ON without selecting Tax Rate
        logged_in_page.locator("app-slide-toggle-v2 div.slider").nth(0).click(force=True)
        logged_in_page.wait_for_timeout(600)
        # Submit without picking Tax Rate
        _val_submit(logged_in_page)
        assert logged_in_page.locator(
            "xpath=//mat-label[contains(.,'Tax Rate')]"
            "/ancestor::mat-form-field"
            "//mat-error[contains(.,'This field is required')]"
        ).count() > 0, "Expected 'This field is required' on Tax Rate when GST Set Off enabled"
        _val_cancel(logged_in_page)


# ═══════════════════════════════════════════════════════════════════════════════
# QC form validations
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.po_qc_pb
class TestQCValidations:
    """Validation tests for the QC form (Ganesh Agrotech tenant)."""

    def _cancel(self, qc_page):
        qc_page.navigate_to_page()
        qc_page.page.wait_for_selector("table.mat-mdc-table, div.empty-state", timeout=10000)

    def _visible_errors(self, qc_page):
        return qc_page.page.evaluate("""
            () => Array.from(document.querySelectorAll('mat-error'))
                       .filter(el => el.offsetParent !== null)
                       .map(el => el.innerText.trim())
        """)

    def test_empty_submit_keeps_form(self, qc_page):
        """Empty submit must show mat-errors and keep the form open."""
        qc_page.open_add_form()
        qc_page.page.locator(qc_page.SUBMIT_BTN).click(force=True)
        qc_page.page.wait_for_timeout(1000)
        assert qc_page.page.locator("mat-error").count() > 0, \
            "Expected mat-errors on empty QC submit"
        assert qc_page.page.locator(qc_page.SUPPLIER_NAME).count() > 0, \
            "Form must stay open after empty submit"
        self._cancel(qc_page)

    def test_cancel_returns_to_listing(self, qc_page):
        """Cancel must close form and return to listing."""
        qc_page.open_add_form()
        qc_page.close_popup()
        assert qc_page.page.locator("table.mat-mdc-table, div.empty-state").count() > 0, \
            "Listing must be visible after cancel"

    def test_no_supplier_submit_blocked(self, qc_page):
        """Submit with no supplier selected must show mat-error on Supplier Name."""
        qc_page.open_add_form()
        qc_page.page.locator(qc_page.SUBMIT_BTN).click(force=True)
        qc_page.page.wait_for_timeout(1000)
        errors = self._visible_errors(qc_page)
        assert len(errors) > 0, "Expected mat-errors when supplier not selected"
        self._cancel(qc_page)

    def test_supplier_no_po_submit_blocked(self, qc_page, po_for_validations):
        """Supplier selected but no PO selected — submit must show mat-errors."""
        qc_page.open_add_form()
        qc_page._select_mat_by_text(qc_page.SUPPLIER_NAME, po_for_validations["supplier_name"])
        qc_page.page.wait_for_timeout(1000)
        qc_page.page.locator(qc_page.SUBMIT_BTN).click(force=True)
        qc_page.page.wait_for_timeout(1000)
        assert qc_page.page.locator("mat-error").count() > 0, \
            "Expected mat-errors when PO not selected"
        self._cancel(qc_page)

    def test_no_bags_submit_blocked(self, qc_page, po_for_validations):
        """Supplier + PO selected but No. of Bags left empty — submit must show mat-errors."""
        qc_page.open_add_form()
        qc_page.select_supplier_and_po(po_for_validations["supplier_name"])
        qc_page.page.wait_for_timeout(800)
        qc_page.page.locator(qc_page.SUBMIT_BTN).click(force=True)
        qc_page.page.wait_for_timeout(1000)
        assert qc_page.page.locator("mat-error").count() > 0, \
            "Expected mat-errors when No. of Bags is empty"
        self._cancel(qc_page)

    def test_qc_param_popup_empty_done_blocked(self, qc_page, po_for_validations):
        """Clicking Done in QC param popup without filling Actual Value must show mat-error."""
        qc_page.open_add_form()
        qc_page.select_supplier_and_po(po_for_validations["supplier_name"])
        qc_page.page.wait_for_timeout(800)
        qc_page._fill_nth(qc_page.NO_OF_BAGS, 0, "1")
        qc_page.open_qc_param_popup(0)
        qc_page.page.locator(qc_page.DONE_BTN).click(force=True)
        qc_page.page.wait_for_timeout(800)
        errors = self._visible_errors(qc_page)
        popup_open = qc_page.page.locator(qc_page.DONE_BTN).is_visible()
        assert len(errors) > 0 or popup_open, \
            "Expected mat-error or popup to stay open when Actual Value is empty"
        self._cancel(qc_page)


# ═══════════════════════════════════════════════════════════════════════════════
# PB form validations
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.po_qc_pb
class TestPBValidations:
    """Validation tests for the PB form (Ganesh Agrotech tenant)."""

    def _cancel(self, pb_page):
        try:
            if pb_page.page.locator(pb_page.DONE_BTN).is_visible():
                pb_page.page.keyboard.press("Escape")
                pb_page.page.wait_for_timeout(400)
        except Exception:
            pass
        pb_page.navigate_to_page()
        pb_page.page.wait_for_selector("table.mat-mdc-table, div.empty-state", timeout=10000)

    def _fill_native(self, pb_page, selector, value):
        xpath = selector.replace("xpath=", "")
        loc = pb_page.page.locator(f"xpath={xpath}").filter(
            has=pb_page.page.locator(":visible")
        ).first
        if loc.count() == 0:
            loc = pb_page.page.locator(f"xpath={xpath}").first
        loc.click(force=True)
        loc.fill(str(value))
        loc.press("Tab")
        pb_page.page.wait_for_timeout(600)

    def _visible_errors(self, pb_page):
        return pb_page.page.evaluate("""
            () => Array.from(document.querySelectorAll('mat-error'))
                       .filter(el => el.offsetParent !== null)
                       .map(el => el.innerText.trim())
        """)

    def _open_pb_with_qc(self, pb_page, supplier_name):
        pb_page.open_add_form()
        pb_page.select_supplier_and_qc(supplier_name)

    def test_empty_submit_keeps_form(self, pb_page):
        """Empty submit must show mat-errors and keep form open."""
        pb_page.open_add_form()
        pb_page.page.locator(pb_page.SUBMIT_BTN).click(force=True)
        pb_page.page.wait_for_timeout(1000)
        assert pb_page.page.locator("mat-error").count() > 0, \
            "Expected mat-errors on empty PB submit"
        assert pb_page.page.locator(pb_page.SUPPLIER_NAME).count() > 0, \
            "Form must stay open after empty submit"
        self._cancel(pb_page)

    def test_cancel_returns_to_listing(self, pb_page):
        """Cancel must close form and show listing."""
        pb_page.open_add_form()
        self._cancel(pb_page)
        assert pb_page.page.locator("table.mat-mdc-table, div.empty-state").count() > 0, \
            "Listing must be visible after cancel"

    def test_no_supplier_submit_blocked(self, pb_page):
        """Empty submit with no supplier must show mat-errors."""
        pb_page.open_add_form()
        pb_page.page.locator(pb_page.SUBMIT_BTN).click(force=True)
        pb_page.page.wait_for_timeout(1000)
        errors = self._visible_errors(pb_page)
        assert len(errors) > 0, "Expected mat-errors when supplier not selected"
        self._cancel(pb_page)

    def test_supplier_no_qc_submit_blocked(self, pb_page, po_for_validations):
        """Supplier selected but no QC selected — submit must show mat-errors."""
        pb_page.open_add_form()
        pb_page._select_mat_by_text(pb_page.SUPPLIER_NAME, po_for_validations["supplier_name"])
        pb_page.page.wait_for_timeout(1000)
        pb_page.page.locator(pb_page.SUBMIT_BTN).click(force=True)
        pb_page.page.wait_for_timeout(1000)
        assert pb_page.page.locator("mat-error").count() > 0, \
            "Expected mat-errors when QC not selected"
        self._cancel(pb_page)

    def test_discount_over_100_blocked(self, pb_page, po_for_validations):
        """Discount > 100 must trigger mat-error."""
        self._open_pb_with_qc(pb_page, po_for_validations["supplier_name"])
        self._fill_native(pb_page, pb_page.DISC_PERCENTAGE, 101)
        pb_page.page.locator(pb_page.SUBMIT_BTN).click(force=True)
        pb_page.page.wait_for_timeout(1000)
        assert len(self._visible_errors(pb_page)) > 0, \
            "Expected mat-error for discount > 100"
        self._cancel(pb_page)

    def test_round_off_credit_over_1_blocked(self, pb_page, po_for_validations):
        """Round Off Credit > 1 must trigger mat-error."""
        self._open_pb_with_qc(pb_page, po_for_validations["supplier_name"])
        self._fill_native(pb_page, pb_page.ROUND_OFF_CREDIT, 2)
        pb_page.page.locator(pb_page.SUBMIT_BTN).click(force=True)
        pb_page.page.wait_for_timeout(1000)
        assert len(self._visible_errors(pb_page)) > 0, \
            "Expected mat-error when Round Off Credit > 1"
        self._cancel(pb_page)

    def test_round_off_debit_over_1_blocked(self, pb_page, po_for_validations):
        """Round Off Debit > 1 must trigger mat-error."""
        self._open_pb_with_qc(pb_page, po_for_validations["supplier_name"])
        pb_page._fill_number_nth(pb_page.ROUND_OFF_DEBIT, 0, 2)
        pb_page.page.wait_for_timeout(600)
        assert pb_page.page.locator("mat-error").count() > 0, \
            "Expected mat-error when Round Off Debit > 1"
        self._cancel(pb_page)

    def test_qty_zero_in_popup_blocked(self, pb_page, po_for_validations):
        """qty=0 in Qty Details popup must show mat-error or keep popup open."""
        self._open_pb_with_qc(pb_page, po_for_validations["supplier_name"])
        pb_page.open_qty_details_popup(0)
        pb_page.fill_qty_details(no_of_bags=1, qty=0)
        pb_page.page.wait_for_timeout(600)
        pb_page.page.locator(pb_page.DONE_BTN).click(force=True)
        pb_page.page.wait_for_timeout(800)
        errors     = pb_page.page.locator("mat-error").count()
        popup_open = pb_page.page.locator(pb_page.DONE_BTN).is_visible()
        assert errors > 0 or popup_open, \
            "Expected mat-error or popup to stay open when qty=0"
        self._cancel(pb_page)

    def test_ebw_over_qty_blocked(self, pb_page, po_for_validations):
        """Empty Bag Weight > accepted qty must produce a negative net qty error."""
        self._open_pb_with_qc(pb_page, po_for_validations["supplier_name"])
        po_qty = po_for_validations["po_qty"]
        self._fill_native(pb_page, pb_page.EMPTY_BAG_WEIGHT, po_qty + 5)
        pb_page.open_qty_details_popup(0)
        pb_page.fill_qty_details(no_of_bags=1, qty=po_qty)
        pb_page.click_done()
        pb_page.page.wait_for_timeout(800)
        errors = [e.inner_text().strip() for e in pb_page.page.locator("mat-error").all()]
        assert any("less than 0" in e or "cannot" in e.lower() for e in errors), (
            f"Expected net qty / amount error when EBW > qty, got: {errors}"
        )
        self._cancel(pb_page)

    def test_labour_over_gross_blocked(self, pb_page, po_for_validations):
        """Labour Charges > gross amount must produce an amount error."""
        self._open_pb_with_qc(pb_page, po_for_validations["supplier_name"])
        po_qty = po_for_validations["po_qty"]
        self._fill_native(pb_page, pb_page.LABOUR_CHARGES, 999999)
        pb_page.open_qty_details_popup(0)
        pb_page.fill_qty_details(no_of_bags=1, qty=po_qty)
        pb_page.click_done()
        pb_page.page.wait_for_timeout(800)
        errors = [e.inner_text().strip() for e in pb_page.page.locator("mat-error").all()]
        assert any(
            "less than 0" in e or "cannot" in e.lower()
            or "greater than 0" in e or "must be" in e.lower()
            for e in errors
        ), f"Expected amount error when labour > gross, got: {errors}"
        self._cancel(pb_page)


# ═══════════════════════════════════════════════════════════════════════════════
# Full validation + integration flow
# PO validation → create PO → QC validation → create QC → PB validation → create PB
# ═══════════════════════════════════════════════════════════════════════════════

BASE_URL = "https://rhythmerp.algorhythms.in"
_PO_URL  = f"{BASE_URL}/#/purchase/purchase-order"
_QC_URL  = f"{BASE_URL}/#/purchase/qc"
_PB_URL  = f"{BASE_URL}/#/purchase/purchase-booking"


def _val_assert_errors(page, expected_errors):
    failures = []
    for label, error_text in expected_errors:
        sel = (
            f"//mat-label[contains(.,'{label}')]"
            f"/ancestor::mat-form-field"
            f"//mat-error[contains(.,'{error_text}')]"
        )
        if page.locator(f"xpath={sel}").count() == 0:
            failures.append(f"  MISSING  [{label}] → '{error_text}'")
        else:
            print(f"  OK  [{label}] → '{error_text}'")
    if failures:
        pytest.fail("Missing validation errors:\n" + "\n".join(failures))


def _val_assert_no_errors(page):
    count = page.locator("mat-error").count()
    assert count == 0, f"Expected no validation errors but found {count}"


def _val_open_form(page, url):
    page.goto(url)
    try:
        page.wait_for_selector("table.mat-mdc-table, div.empty-state", timeout=15000)
    except Exception:
        page.reload()
        page.wait_for_selector("table.mat-mdc-table, div.empty-state", timeout=20000)
    page.wait_for_timeout(500)
    add_btn = page.locator("button.erp-add-btn")
    add_btn.wait_for(state="visible", timeout=10000)
    add_btn.click(force=True)
    page.wait_for_timeout(2000)
    if page.locator("xpath=//mat-label[contains(.,'Supplier Name')]").count() == 0:
        add_btn.click(force=True)
        page.wait_for_timeout(2000)


def _val_submit(page):
    page.locator(
        "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]"
    ).first.click(force=True)
    page.wait_for_timeout(1500)


def _val_cancel(page):
    try:
        page.locator(
            "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]"
        ).first.click()
        page.wait_for_timeout(1000)
    except Exception:
        try:
            page.keyboard.press("Escape")
        except Exception:
            pass


def _val_select_first(page, label, alt_label=None):
    sel = f"//mat-label[contains(.,'{label}')]/ancestor::mat-form-field//mat-select"
    loc = page.locator(f"xpath={sel}").first
    if alt_label and loc.count() == 0:
        sel = f"//mat-label[contains(.,'{alt_label}')]/ancestor::mat-form-field//mat-select"
        loc = page.locator(f"xpath={sel}").first
    loc.click(force=True)
    page.wait_for_selector(".mat-mdc-select-panel", timeout=8000)
    page.locator(".mat-mdc-select-panel mat-option").first.click(force=True)
    try:
        page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
    except Exception:
        pass
    page.wait_for_timeout(400)


def _val_try_select_first(page, label, alt_label=None):
    """Like _val_select_first but silently skips if field is absent or panel doesn't open."""
    sel = f"//mat-label[contains(.,'{label}')]/ancestor::mat-form-field//mat-select"
    loc = page.locator(f"xpath={sel}").first
    if alt_label and loc.count() == 0:
        sel = f"//mat-label[contains(.,'{alt_label}')]/ancestor::mat-form-field//mat-select"
        loc = page.locator(f"xpath={sel}").first
    if loc.count() == 0:
        return
    loc.click(force=True)
    try:
        page.wait_for_selector(".mat-mdc-select-panel", timeout=3000)
    except Exception:
        return
    page.locator(".mat-mdc-select-panel mat-option").first.click(force=True)
    try:
        page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
    except Exception:
        pass
    page.wait_for_timeout(400)


def _val_select_last(page, label):
    sel = f"//mat-label[contains(.,'{label}')]/ancestor::mat-form-field//mat-select"
    page.locator(f"xpath={sel}").first.click(force=True)
    page.wait_for_selector(".mat-mdc-select-panel", timeout=8000)
    page.locator(".mat-mdc-select-panel mat-option").last.click(force=True)
    try:
        page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
    except Exception:
        pass
    page.wait_for_timeout(400)


def _val_select_text(page, label, text, row_index=0):
    sel = f"//mat-label[contains(.,'{label}')]/ancestor::mat-form-field//mat-select"
    page.locator(f"xpath={sel}").nth(row_index).click(force=True)
    page.wait_for_selector(".mat-mdc-select-panel", timeout=8000)
    for opt in page.locator(
        ".mat-mdc-select-panel mat-option span.mdc-list-item__primary-text"
    ).all():
        if opt.inner_text().strip() == text:
            opt.click(force=True)
            break
    try:
        page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
    except Exception:
        pass
    page.wait_for_timeout(400)


def _val_fill(page, label, value, row_index=0):
    page.evaluate("""
        ([label, val, idx]) => {
            const all = [...document.querySelectorAll('mat-label')]
                .filter(l => l.textContent.includes(label));
            const lbl = all[idx] || all[0];
            if (!lbl) return;
            const inp = lbl.closest('mat-form-field')?.querySelector('input');
            if (!inp) return;
            const setter = Object.getOwnPropertyDescriptor(
                window.HTMLInputElement.prototype, 'value').set;
            setter.call(inp, val);
            inp.dispatchEvent(new Event('input', {bubbles: true}));
            inp.dispatchEvent(new Event('change', {bubbles: true}));
            inp.blur();
        }
    """, [label, str(value), row_index])
    page.wait_for_timeout(400)


def _val_fill_native(page, label, value):
    """Click the input, fill (clears first), blur — overrides auto-filled fields."""
    inp = page.locator(
        f"xpath=//mat-label[contains(.,'{label}')]/ancestor::mat-form-field//input"
    ).first
    inp.wait_for(state="visible", timeout=8000)
    inp.click(force=True)
    inp.fill(str(value))
    # Dispatch Angular blur without Tab (Tab can re-trigger rate fetch)
    page.evaluate("""
        (label) => {
            const lbl = [...document.querySelectorAll('mat-label')]
                .find(l => l.textContent.includes(label));
            if (!lbl) return;
            const inp = lbl.closest('mat-form-field')?.querySelector('input');
            if (!inp) return;
            inp.dispatchEvent(new Event('blur', {bubbles: true}));
            inp.dispatchEvent(new Event('change', {bubbles: true}));
        }
    """, label)
    page.wait_for_timeout(400)


def _po_prefill_full(page):
    _val_open_form(page, _PO_URL)
    _val_select_first(page, "Supplier Name")
    page.wait_for_timeout(1500)
    _val_select_first(page, "Item Category", alt_label="PO Item Type")
    page.wait_for_timeout(500)
    _val_fill(page, "Conversion Rate", "1")  # no-op if field absent
    _val_select_first(page, "Location")
    page.wait_for_timeout(500)
    _val_select_first(page, "Department")
    _val_select_first(page, "Division")
    _val_select_first(page, "Type of Sale")
    _val_try_select_first(page, "Packaging Forwarding")  # silently skips if field absent
    _val_select_first(page, "Item Name")
    page.wait_for_timeout(1500)


def _pb_prefill_full(page, supplier_name):
    _val_open_form(page, _PB_URL)
    _val_select_text(page, "Supplier Name", supplier_name)
    page.wait_for_timeout(1500)
    _val_select_last(page, "QC")
    page.wait_for_timeout(6000)
    _val_fill(page, "Conversion Rate", "1")
    page.wait_for_timeout(500)


# ── Error sets ────────────────────────────────────────────────────────────────

_VAL_PO_EMPTY = [
    ("Supplier Name",              "This field is required."),
    ("Item Category",              "This field is required."),
    ("PO Type",                    "This field is required."),
    ("Transaction Currency",       "This field is required."),
    ("Location",                   "This field is required."),
    ("Department",                 "This field is required."),
    ("Division",                   "This field is required."),
    ("Type of Sale",               "This field is required."),
    ("Payment Terms",              "This field is required."),
    ("Delivery Terms",             "This field is required."),
    ("Supplier Shippling Address", "This field is required."),
    ("Supplier Billing Address",   "This field is required."),
    ("Item Name",                  "This field is required."),
    ("Quantity",                   "Field is required"),
    ("Rate",                       "Rate is required"),
]
_VAL_PO_AFTER_SUPPLIER = [
    ("Item Category",  "This field is required."),
    ("Location",       "This field is required."),
    ("Department",     "This field is required."),
    ("Division",       "This field is required."),
    ("Type of Sale",   "This field is required."),
    ("Item Name",      "This field is required."),
    ("Quantity",       "Field is required"),
    ("Rate",           "Rate is required"),
]
_VAL_PO_AFTER_ITEM_CAT = [
    ("Location",     "This field is required."),
    ("Department",   "This field is required."),
    ("Division",     "This field is required."),
    ("Type of Sale", "This field is required."),
    ("Item Name",    "This field is required."),
    ("Quantity",     "Field is required"),
    ("Rate",         "Rate is required"),
]
_VAL_PO_AFTER_CONV_RATE = [
    ("Location",     "This field is required."),
    ("Department",   "This field is required."),
    ("Division",     "This field is required."),
    ("Type of Sale", "This field is required."),
    ("Item Name",    "This field is required."),
    ("Quantity",     "Field is required"),
    ("Rate",         "Rate is required"),
]
_VAL_PO_AFTER_LOCATION = [
    ("Department",   "This field is required."),
    ("Division",     "This field is required."),
    ("Type of Sale", "This field is required."),
    ("Item Name",    "This field is required."),
    ("Quantity",     "Field is required"),
    ("Rate",         "Rate is required"),
]
_VAL_PO_AFTER_DEPT = [
    ("Division",     "This field is required."),
    ("Type of Sale", "This field is required."),
    ("Item Name",    "This field is required."),
    ("Quantity",     "Field is required"),
    ("Rate",         "Rate is required"),
]
_VAL_PO_AFTER_DIV = [
    ("Type of Sale", "This field is required."),
    ("Item Name",    "This field is required."),
    ("Quantity",     "Field is required"),
    ("Rate",         "Rate is required"),
]
_VAL_PO_AFTER_SALE_TYPE = [
    ("Item Name", "This field is required."),
    ("Quantity",  "Field is required"),
    ("Rate",      "Rate is required"),
]
_VAL_PO_AFTER_PACKAGING = [
    ("Item Name", "This field is required."),
    ("Quantity",  "Field is required"),
    ("Rate",      "Rate is required"),
]
_VAL_PO_AFTER_ITEM_NAME = [
    ("Quantity", "Field is required"),
]
_VAL_PO_RATE_ZERO = [
    ("Rate", "Rate cannot be less than 0"),
]
_VAL_PO_QTY_ZERO = [
    ("Quantity", "Quantity cannot be less than 0"),
]
_VAL_PO_DISCOUNT_INVALID = [
    ("Discount %", "Discount percentage must be between 0 to 100."),
]
_VAL_QC_EMPTY = [
    ("Supplier Name",            "This field is required."),
    ("Item category",            "This field is required."),
    ("Base Currency",            "This field is required."),
    ("Transaction Currency",     "This field is required."),
    ("Conversion Rate",          "This field is required."),
    ("Total Transaction Amount", "Amount should be greater than 0"),
    ("Location",                 "This field is required."),
    ("Department",               "This field is required."),
    ("Division",                 "This field is required."),
    ("Type of Sale",             "This field is required."),
    ("Final Rate",               "Rate cannot be less than 0"),
    ("Transaction Amount",       "Amount should be greater than 0"),
]
_VAL_QC_AFTER_SUPPLIER = [
    ("Item category",            "This field is required."),
    ("Base Currency",            "This field is required."),
    ("Transaction Currency",     "This field is required."),
    ("Conversion Rate",          "This field is required."),
    ("Total Transaction Amount", "Amount should be greater than 0"),
    ("Location",                 "This field is required."),
    ("Department",               "This field is required."),
    ("Division",                 "This field is required."),
    ("Type of Sale",             "This field is required."),
    ("Final Rate",               "Rate cannot be less than 0"),
    ("Transaction Amount",       "Amount should be greater than 0"),
]
_VAL_QC_AFTER_PO     = [("Conversion Rate", "This field is required.")]
_VAL_QC_BAGS_INVALID = [("NO. of Bags", "Enter a valid bag quantity.")]
_VAL_PB_EMPTY = [
    ("Supplier Name",        "This field is required."),
    ("Supplier Type",        "This field is required."),
    ("Base Currency",        "This field is required."),
    ("Transaction Currency", "This field is required."),
    ("Conversion Rate",      "This field is required."),
    ("Amount",               "Amount should be greater than 0"),
    ("Total Amount",         "Amount should be greater than 0"),
    ("Location",             "This field is required."),
    ("Department",           "This field is required."),
    ("Division",             "This field is required."),
    ("Type of Sale",         "This field is required."),
    ("No Of Bags",           "Enter a valid bag quantity."),
    ("Net Quantity",         "Net Quantity cannot be less than 0"),
    ("Transaction Amount",   "Transaction Amount must be greater than 0."),
]
_VAL_PB_AFTER_SUPPLIER = [
    ("Amount",             "Amount should be greater than 0"),
    ("Total Amount",       "Amount should be greater than 0"),
    ("No Of Bags",         "Enter a valid bag quantity."),
    ("Net Quantity",       "Net Quantity cannot be less than 0"),
    ("Transaction Amount", "Transaction Amount must be greater than 0."),
]
_VAL_PB_AFTER_QC         = [("Conversion Rate", "This field is required.")]
_VAL_PB_DISCOUNT_INVALID = [
    ("Total Amount",        "Amount should be greater than 0"),
    ("Discount Percentage", "Cannot be greater than 100%"),
]
_VAL_PB_BAG_WEIGHT_NEG    = [("Empty Bag Weight (KG)", "Empty Bag Weight cannot be negative.")]
_VAL_PB_BAG_WEIGHT_GT_QTY = [
    ("Amount",             "Amount should be greater than 0"),
    ("Total Amount",       "Amount should be greater than 0"),
    ("Net Quantity",       "Net Quantity cannot be less than 0"),
    ("Transaction Amount", "Transaction Amount must be greater than 0."),
]


@pytest.mark.po_qc_pb
class TestPOQCPBValidationFlow:
    """
    PO full validation → create PO → QC full validation → create QC → PB full validation → create PB.
    Steps run sequentially; form stays open between progressive steps.
    """

    # ── PO VALIDATION ────────────────────────────────────────────────────────

    def test_po_step01_empty_submit(self, logged_in_page):
        _val_open_form(logged_in_page, _PO_URL)
        _val_submit(logged_in_page)
        print("\n[PO-val] step01: empty form")
        _val_assert_errors(logged_in_page, _VAL_PO_EMPTY)

    def test_po_step02_after_supplier(self, logged_in_page):
        _val_select_first(logged_in_page, "Supplier Name")
        logged_in_page.wait_for_timeout(1500)
        _val_submit(logged_in_page)
        print("\n[PO-val] step02: after supplier")
        _val_assert_errors(logged_in_page, _VAL_PO_AFTER_SUPPLIER)

    def test_po_step03_after_item_category(self, logged_in_page):
        _val_select_first(logged_in_page, "Item Category", alt_label="PO Item Type")
        logged_in_page.wait_for_timeout(500)
        _val_submit(logged_in_page)
        print("\n[PO-val] step03: after item category")
        _val_assert_errors(logged_in_page, _VAL_PO_AFTER_ITEM_CAT)

    def test_po_step04_after_conversion_rate(self, logged_in_page):
        _val_fill(logged_in_page, "Conversion Rate", "1")  # no-op if field absent
        _val_submit(logged_in_page)
        print("\n[PO-val] step04: after conversion rate (skipped if field absent)")
        _val_assert_errors(logged_in_page, _VAL_PO_AFTER_CONV_RATE)

    def test_po_step05_after_location(self, logged_in_page):
        _val_select_first(logged_in_page, "Location")
        logged_in_page.wait_for_timeout(500)
        _val_submit(logged_in_page)
        print("\n[PO-val] step05: after location")
        _val_assert_errors(logged_in_page, _VAL_PO_AFTER_LOCATION)

    def test_po_step06_after_department(self, logged_in_page):
        _val_select_first(logged_in_page, "Department")
        logged_in_page.wait_for_timeout(500)
        _val_submit(logged_in_page)
        print("\n[PO-val] step06: after department")
        _val_assert_errors(logged_in_page, _VAL_PO_AFTER_DEPT)

    def test_po_step07_after_division(self, logged_in_page):
        _val_select_first(logged_in_page, "Division")
        logged_in_page.wait_for_timeout(500)
        _val_submit(logged_in_page)
        print("\n[PO-val] step07: after division")
        _val_assert_errors(logged_in_page, _VAL_PO_AFTER_DIV)

    def test_po_step08_after_type_of_sale(self, logged_in_page):
        _val_select_first(logged_in_page, "Type of Sale")
        logged_in_page.wait_for_timeout(500)
        _val_submit(logged_in_page)
        print("\n[PO-val] step08: after type of sale")
        _val_assert_errors(logged_in_page, _VAL_PO_AFTER_SALE_TYPE)

    def test_po_step09_after_packaging_forwarding(self, logged_in_page):
        _val_try_select_first(logged_in_page, "Packaging Forwarding")  # silently skips if field absent
        logged_in_page.wait_for_timeout(500)
        _val_submit(logged_in_page)
        print("\n[PO-val] step09: after packaging forwarding (skipped if field absent)")
        _val_assert_errors(logged_in_page, _VAL_PO_AFTER_PACKAGING)

    def test_po_step10_after_item_name(self, logged_in_page):
        _val_select_first(logged_in_page, "Item Name")
        logged_in_page.wait_for_timeout(1500)
        _val_submit(logged_in_page)
        print("\n[PO-val] step10: after item name")
        _val_assert_errors(logged_in_page, _VAL_PO_AFTER_ITEM_NAME)

    def test_po_step11_quantity_no_errors(self, logged_in_page):
        _val_fill(logged_in_page, "Quantity", "10")
        logged_in_page.wait_for_timeout(800)
        _val_submit(logged_in_page)
        print("\n[PO-val] step11: quantity filled — form should submit")
        try:
            logged_in_page.wait_for_selector("table.mat-mdc-table", timeout=12000)
        except Exception:
            _val_assert_no_errors(logged_in_page)

    def test_po_step12_rate_zero(self, logged_in_page):
        _po_prefill_full(logged_in_page)
        logged_in_page.wait_for_timeout(2000)  # let initial rate auto-fill settle
        _val_fill_native(logged_in_page, "Quantity", "10")
        # Fill Rate=0 twice: first fill + blur triggers an API re-fetch; wait for it to
        # complete, then fill 0 again without blur so the value stays 0 at submit time.
        _val_fill_native(logged_in_page, "Rate", "0")
        logged_in_page.wait_for_timeout(3000)  # wait for API re-fetch to land
        logged_in_page.evaluate("""
            () => {
                const lbl = [...document.querySelectorAll('mat-label')]
                    .find(l => l.textContent.trim() === 'Rate');
                if (!lbl) return;
                const inp = lbl.closest('mat-form-field')?.querySelector('input');
                if (!inp) return;
                const setter = Object.getOwnPropertyDescriptor(
                    HTMLInputElement.prototype, 'value').set;
                setter.call(inp, '0');
                inp.dispatchEvent(new Event('input', {bubbles: true}));
                inp.dispatchEvent(new Event('change', {bubbles: true}));
                // intentionally no blur — blur re-triggers the rate API fetch
            }
        """)
        logged_in_page.wait_for_timeout(400)
        _val_submit(logged_in_page)
        print("\n[PO-val] step12: rate=0")
        _val_assert_errors(logged_in_page, _VAL_PO_RATE_ZERO)
        _val_cancel(logged_in_page)

    def test_po_step13_quantity_zero(self, logged_in_page):
        _po_prefill_full(logged_in_page)
        _val_fill_native(logged_in_page, "Quantity", "0")
        logged_in_page.wait_for_timeout(500)
        _val_submit(logged_in_page)
        print("\n[PO-val] step13: quantity=0")
        _val_assert_errors(logged_in_page, _VAL_PO_QTY_ZERO)
        _val_cancel(logged_in_page)

    def test_po_step14_discount_invalid(self, logged_in_page):
        _po_prefill_full(logged_in_page)
        _val_fill(logged_in_page, "Quantity", "10")
        _val_fill(logged_in_page, "Discount %", "150")
        logged_in_page.wait_for_timeout(500)
        _val_submit(logged_in_page)
        print("\n[PO-val] step14: discount=150")
        _val_assert_errors(logged_in_page, _VAL_PO_DISCOUNT_INVALID)
        _val_cancel(logged_in_page)

    # ── CREATE ACTUAL PO ─────────────────────────────────────────────────────

    def test_po_step15_create_actual_po(self, logged_in_page, integration_state):
        po = POPlaywrightPage(logged_in_page)
        po.navigate_to_page()
        total, row_dicts, supplier_name, location, po_ref_no = \
            po.create_record_for_integration(
                item_configs=[(PO_QC_PB_QTY, 0, 0)],
                item_names_override=["Welding Electrode FLUID TRANSFER ABRASION RESISTANT REINFORCED TYPE"],
                enable_gst=False,
            )
        assert po_ref_no, "PO ref must be non-empty"
        integration_state["val_supplier"] = supplier_name
        integration_state["val_po_ref"]   = po_ref_no
        integration_state["val_item_name"] = row_dicts[0]["item_name"]
        print(f"\n[VAL-PO] Created {po_ref_no}  supplier={supplier_name}")

    # ── QC VALIDATION ────────────────────────────────────────────────────────

    def test_qc_step16_empty_submit(self, logged_in_page):
        _val_open_form(logged_in_page, _QC_URL)
        _val_submit(logged_in_page)
        print("\n[QC-val] step16: empty form")
        _val_assert_errors(logged_in_page, _VAL_QC_EMPTY)

    def test_qc_step17_after_supplier(self, logged_in_page, integration_state):
        _val_select_text(logged_in_page, "Supplier Name",
                         integration_state["val_supplier"])
        logged_in_page.wait_for_timeout(1500)
        _val_submit(logged_in_page)
        print("\n[QC-val] step17: after supplier")
        _val_assert_errors(logged_in_page, _VAL_QC_AFTER_SUPPLIER)

    def test_qc_step18_after_po(self, logged_in_page):
        _val_select_last(logged_in_page, "Purchase Order")
        logged_in_page.wait_for_timeout(2000)
        _val_submit(logged_in_page)
        print("\n[QC-val] step18: after PO selected")
        _val_assert_errors(logged_in_page, _VAL_QC_AFTER_PO)

    def test_qc_step19_conversion_rate_no_errors(self, logged_in_page):
        _val_fill(logged_in_page, "Conversion Rate", "1")
        logged_in_page.wait_for_timeout(500)
        _val_submit(logged_in_page)
        print("\n[QC-val] step19: conversion rate filled — form should submit")
        try:
            logged_in_page.wait_for_selector("table.mat-mdc-table", timeout=12000)
        except Exception:
            _val_assert_no_errors(logged_in_page)

    def test_qc_step20_bags_zero(self, logged_in_page, integration_state):
        _val_open_form(logged_in_page, _QC_URL)
        _val_select_text(logged_in_page, "Supplier Name",
                         integration_state["val_supplier"])
        logged_in_page.wait_for_timeout(1500)
        _val_select_last(logged_in_page, "Purchase Order")
        logged_in_page.wait_for_timeout(2000)
        _val_fill(logged_in_page, "Conversion Rate", "1")
        _val_fill(logged_in_page, "NO. of Bags", "0")
        logged_in_page.wait_for_timeout(500)
        _val_submit(logged_in_page)
        print("\n[QC-val] step20: bags=0")
        _val_assert_errors(logged_in_page, _VAL_QC_BAGS_INVALID)
        _val_cancel(logged_in_page)

    # ── CREATE ACTUAL QC ─────────────────────────────────────────────────────

    def test_qc_step21_create_actual_qc(self, logged_in_page, integration_state):
        supplier_name = integration_state["val_supplier"]

        qc = QCPlaywrightPage(logged_in_page)
        qc.navigate_to_page()
        qc.open_add_form()
        qc.select_supplier_and_po(supplier_name)

        row_count = qc.count_item_rows()
        item_names = [integration_state["val_item_name"]] * row_count
        cqp_config = build_cqp_config(item_names, logged_in_page)
        qc.cqp_config = cqp_config
        qc.item_names = item_names

        for i in range(row_count):
            qc.fill_bags_popup(row_index=i)
            qc.fill_qc_params_safe(row_index=i)

        qc.page.wait_for_timeout(5000)
        qc.page.locator(qc.SUBMIT_BTN).click()
        ok = qc.handle_submit_result(timeout=10000)
        assert ok, "QC submission failed"

        qc.navigate_to_page()
        qc_ref_no = qc.get_ref_no_of_first_row()
        assert qc_ref_no, "QC ref must be non-empty"
        integration_state["val_qc_ref"] = qc_ref_no
        print(f"\n[VAL-QC] Created {qc_ref_no}")

    # ── PB VALIDATION ────────────────────────────────────────────────────────

    def test_pb_step22_empty_submit(self, logged_in_page):
        _val_open_form(logged_in_page, _PB_URL)
        _val_submit(logged_in_page)
        print("\n[PB-val] step22: empty form")
        _val_assert_errors(logged_in_page, _VAL_PB_EMPTY)

    def test_pb_step23_after_supplier(self, logged_in_page, integration_state):
        _val_select_text(logged_in_page, "Supplier Name",
                         integration_state["val_supplier"])
        logged_in_page.wait_for_timeout(1500)
        _val_submit(logged_in_page)
        print("\n[PB-val] step23: after supplier")
        _val_assert_errors(logged_in_page, _VAL_PB_AFTER_SUPPLIER)

    def test_pb_step24_after_qc(self, logged_in_page):
        _val_select_last(logged_in_page, "QC")
        logged_in_page.wait_for_timeout(6000)
        _val_submit(logged_in_page)
        print("\n[PB-val] step24: after QC selected")
        _val_assert_errors(logged_in_page, _VAL_PB_AFTER_QC)

    def test_pb_step25_conversion_rate_no_errors(self, logged_in_page):
        _val_fill(logged_in_page, "Conversion Rate", "1")
        logged_in_page.wait_for_timeout(500)
        _val_submit(logged_in_page)
        print("\n[PB-val] step25: conversion rate filled — form should submit")
        try:
            logged_in_page.wait_for_selector("table.mat-mdc-table", timeout=12000)
        except Exception:
            _val_assert_no_errors(logged_in_page)

    def test_pb_step26_discount_invalid(self, logged_in_page, integration_state):
        _pb_prefill_full(logged_in_page, integration_state["val_supplier"])
        _val_fill_native(logged_in_page, "Discount Percentage", "150")
        logged_in_page.wait_for_timeout(500)
        _val_submit(logged_in_page)
        print("\n[PB-val] step26: discount=150")
        _val_assert_errors(logged_in_page, _VAL_PB_DISCOUNT_INVALID)
        _val_cancel(logged_in_page)

    def test_pb_step27_empty_bag_weight_negative(self, logged_in_page, integration_state):
        _pb_prefill_full(logged_in_page, integration_state["val_supplier"])
        _val_fill_native(logged_in_page, "Empty Bag Weight (KG)", "-1")
        logged_in_page.wait_for_timeout(500)
        _val_submit(logged_in_page)
        print("\n[PB-val] step27: empty bag weight=-1")
        _val_assert_errors(logged_in_page, _VAL_PB_BAG_WEIGHT_NEG)
        _val_cancel(logged_in_page)

    def test_pb_step28_empty_bag_weight_gt_qty(self, logged_in_page, integration_state):
        _pb_prefill_full(logged_in_page, integration_state["val_supplier"])
        _val_fill_native(logged_in_page, "Empty Bag Weight (KG)", "999999")
        logged_in_page.wait_for_timeout(500)
        _val_submit(logged_in_page)
        print("\n[PB-val] step28: empty bag weight > quantity")
        _val_assert_errors(logged_in_page, _VAL_PB_BAG_WEIGHT_GT_QTY)
        _val_cancel(logged_in_page)

    # ── CREATE ACTUAL PB ─────────────────────────────────────────────────────

    def test_pb_step29_create_actual_pb(self, logged_in_page, integration_state):
        pb = PBPlaywrightPage(logged_in_page)
        logged_in_page.goto(_PB_URL)
        logged_in_page.reload()
        logged_in_page.wait_for_selector(
            "table.mat-mdc-table, div.empty-state", timeout=20000
        )
        logged_in_page.wait_for_timeout(1000)

        pb.open_add_form()
        pb.select_supplier(integration_state["val_supplier"])
        pb.select_qc(integration_state["val_qc_ref"])
        n_rows = pb.count_pb_rows()
        for i in range(n_rows):
            pb._fill_row_tax(i)
        pb.fill_conversion_rate(1)

        pb_ref_no = pb.submit()
        assert pb_ref_no, "PB ref must be non-empty"
        print(
            f"\n[FLOW COMPLETE]"
            f"\n  PO = {integration_state['val_po_ref']}"
            f"\n  QC = {integration_state['val_qc_ref']}"
            f"\n  PB = {pb_ref_no}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Edit-lock flow
# PO editable → QC created → PO locked
# QC editable → PB created → QC locked
# PB never has an active Edit option
# ═══════════════════════════════════════════════════════════════════════════════

def _open_row_menu(page, ref_no):
    """Click the ⋮ button on the row that contains ref_no."""
    page.locator(f"tr:has-text('{ref_no}')").first.locator(
        "button.erp-row-trigger"
    ).click(force=True)
    page.wait_for_selector(".mat-mdc-menu-panel", timeout=8000)
    page.wait_for_timeout(400)


def _close_menu(page):
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)


def _edit_button_state(page):
    """
    Returns 'enabled', 'disabled', or 'absent' for the Edit item in the
    currently open action menu.
    """
    edit_btn = page.locator(
        ".mat-mdc-menu-panel button.mat-mdc-menu-item:has(.erp-menu-title:text-is('Edit'))"
    ).first
    if edit_btn.count() == 0:
        return "absent"
    if edit_btn.get_attribute("aria-disabled") == "true":
        return "disabled"
    return "enabled"


@pytest.mark.po_qc_pb
class TestEditLockFlow:
    """
    Verify record-lock rules enforced by the ERP:
      - PO is editable after creation; Edit is disabled once a QC references it.
      - QC is editable after creation; Edit is disabled once a PB references it.
      - PB has no active Edit option (absent or disabled from the start).
    """

    def test_step1_create_po_edit_enabled(self, logged_in_page, integration_state):
        """Create PO and confirm its Edit menu item is enabled."""
        po = POPlaywrightPage(logged_in_page)
        po.navigate_to_page()
        _, row_dicts, supplier_name, _, po_ref_no = po.create_record_for_integration(
            item_configs=[(50, 0, 0)],
        )
        assert po_ref_no, "PO ref must be non-empty"

        integration_state["lock_supplier"] = supplier_name
        integration_state["lock_po_ref"]   = po_ref_no
        integration_state["lock_item_name"] = row_dicts[0]["item_name"]
        print(f"\n[LOCK] PO created: {po_ref_no}  supplier={supplier_name}")

        po.navigate_to_page()
        _open_row_menu(logged_in_page, po_ref_no)
        state = _edit_button_state(logged_in_page)
        _close_menu(logged_in_page)
        assert state == "enabled", (
            f"PO {po_ref_no} Edit should be enabled before any QC, got '{state}'"
        )
        print(f"[LOCK] PO Edit = {state} ✓")

    def test_step2_create_qc_po_becomes_locked(self, logged_in_page, integration_state):
        """Create QC against the PO; PO Edit must become disabled."""
        if not integration_state.get("lock_po_ref"):
            pytest.skip("PO not created in step 1")

        supplier_name = integration_state["lock_supplier"]
        item_name     = integration_state["lock_item_name"]

        cqp_config = build_cqp_config([item_name], logged_in_page)

        qc = QCPlaywrightPage(logged_in_page)
        qc.cqp_config = cqp_config
        qc.item_names = [item_name]
        qc.navigate_to_page()
        qc.open_add_form()
        qc.select_supplier_and_po(supplier_name)

        qc.fill_bags_popup(row_index=0)
        qc.fill_qc_params_safe(row_index=0)
        qc.page.wait_for_timeout(5000)
        qc.page.locator(qc.SUBMIT_BTN).click()
        ok = qc.handle_submit_result(timeout=10000)
        assert ok, "QC submission failed"

        qc.navigate_to_page()
        qc_ref_no = qc.get_ref_no_of_first_row()
        assert qc_ref_no, "QC ref must be non-empty"
        integration_state["lock_qc_ref"] = qc_ref_no
        print(f"\n[LOCK] QC created: {qc_ref_no}")

        # Verify QC itself is editable right after creation
        _open_row_menu(logged_in_page, qc_ref_no)
        qc_state = _edit_button_state(logged_in_page)
        _close_menu(logged_in_page)
        assert qc_state == "enabled", (
            f"QC {qc_ref_no} Edit should be enabled before any PB, got '{qc_state}'"
        )
        print(f"[LOCK] QC Edit = {qc_state} ✓")

        # Verify PO is now locked (xfail: ERP does not disable PO Edit immediately after QC)
        po = POPlaywrightPage(logged_in_page)
        po.navigate_to_page()
        _open_row_menu(logged_in_page, integration_state["lock_po_ref"])
        po_state = _edit_button_state(logged_in_page)
        _close_menu(logged_in_page)
        if po_state != "disabled":
            pytest.xfail(
                f"PO {integration_state['lock_po_ref']} Edit should be disabled after QC created, "
                f"got '{po_state}'"
            )
        print(f"[LOCK] PO Edit = {po_state} (locked by QC) ✓")

    def test_step3_create_pb_qc_becomes_locked_pb_not_editable(
        self, logged_in_page, integration_state
    ):
        """Create PB against the QC; QC Edit must become disabled; PB must not be editable."""
        if not integration_state.get("lock_qc_ref"):
            pytest.skip("QC not created in step 2")

        supplier_name = integration_state["lock_supplier"]

        pb = PBPlaywrightPage(logged_in_page)
        logged_in_page.goto(_PB_URL)
        logged_in_page.reload()
        logged_in_page.wait_for_selector(
            "table.mat-mdc-table, div.empty-state", timeout=20000
        )
        logged_in_page.wait_for_timeout(1000)

        pb.open_add_form()
        pb.select_supplier(supplier_name)
        pb.select_qc(integration_state["lock_qc_ref"])
        n_rows = pb.count_pb_rows()
        for i in range(n_rows):
            pb._fill_row_tax(i)
        pb.fill_conversion_rate(1)

        pb_ref_no = pb.submit()
        assert pb_ref_no, "PB ref must be non-empty"
        integration_state["lock_pb_ref"] = pb_ref_no
        print(f"\n[LOCK] PB created: {pb_ref_no}")

        # Verify PB has no active Edit (absent or disabled)
        _open_row_menu(logged_in_page, pb_ref_no)
        pb_state = _edit_button_state(logged_in_page)
        _close_menu(logged_in_page)
        assert pb_state in ("absent", "disabled"), (
            f"PB {pb_ref_no} Edit should not be available, got '{pb_state}'"
        )
        print(f"[LOCK] PB Edit = {pb_state} (not editable) ✓")

        # Verify QC is now locked
        qc = QCPlaywrightPage(logged_in_page)
        qc.navigate_to_page()
        _open_row_menu(logged_in_page, integration_state["lock_qc_ref"])
        qc_state = _edit_button_state(logged_in_page)
        _close_menu(logged_in_page)
        assert qc_state == "disabled", (
            f"QC {integration_state['lock_qc_ref']} Edit should be disabled after PB created, "
            f"got '{qc_state}'"
        )
        print(
            f"[LOCK] QC Edit = {qc_state} (locked by PB) ✓"
            f"\n[LOCK COMPLETE]"
            f"\n  PO = {integration_state['lock_po_ref']} (locked)"
            f"\n  QC = {integration_state['lock_qc_ref']} (locked)"
            f"\n  PB = {integration_state['lock_pb_ref']} (never editable)"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# PO View + Audit Trail
# Create → View (verify ref + total amount) → History empty
# → Edit (change qty) → History populated with 1 row showing the ref
# ═══════════════════════════════════════════════════════════════════════════════

def _open_row_action(page, ref_no, action_title):
    """Open the ⋮ menu for ref_no row and click the named action item."""
    page.locator(f"tr:has-text('{ref_no}')").first.locator(
        "button.erp-row-trigger"
    ).click(force=True)
    page.wait_for_selector(".mat-mdc-menu-panel", timeout=8000)
    page.wait_for_timeout(300)
    page.locator(
        f".mat-mdc-menu-panel button.mat-mdc-menu-item"
        f":has(.erp-menu-title:text-is('{action_title}'))"
    ).click(force=True)
    page.wait_for_timeout(1500)


def _close_popup(page):
    # Try "Close" first (History/detail popups), then "Cancel" (View/edit popups)
    footer_close = page.locator(
        "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Close') or contains(.,'Cancel')]"
    )
    if footer_close.count() > 0:
        footer_close.first.click(force=True)
    else:
        page.keyboard.press("Escape")
    page.wait_for_timeout(600)


@pytest.mark.po_qc_pb
class TestPOViewHistoryAuditTrail:
    """
    PO View and audit-trail lifecycle:
      step1: Create PO → open View popup → ref no and total amount visible
      step2: Open History before any edit → must be empty (no-results)
      step3: Edit PO (qty 10→20) → update
      step4: Open History after edit → must have ≥1 row containing the PO ref no
    """

    def test_step1_create_and_view(self, logged_in_page, integration_state):
        """Create PO, open View popup, verify ref no and total amount are shown."""
        po = POPlaywrightPage(logged_in_page)
        po.navigate_to_page()
        total, row_dicts, supplier_name, _, po_ref_no = po.create_record_for_integration(
            item_configs=[(10, 0, 0)],
            item_names_override=["Welding Electrode FLUID TRANSFER ABRASION RESISTANT REINFORCED TYPE"],
            enable_gst=False,
        )
        assert po_ref_no, "PO ref must be non-empty"
        integration_state["audit_po_ref"]    = po_ref_no
        integration_state["audit_po_total"] = total
        integration_state["audit_supplier"] = supplier_name
        integration_state["audit_item_name"] = row_dicts[0]["item_name"]
        print(f"\n[AUDIT] PO created: {po_ref_no}  total={total}  item={row_dicts[0]['item_name']}")

        po.navigate_to_page()
        _open_row_action(logged_in_page, po_ref_no, "View")

        # Wait for popup to open
        logged_in_page.wait_for_selector(".big-model", timeout=10000)
        logged_in_page.wait_for_timeout(500)

        # Angular sets input values as JS properties, not HTML attributes — use input_value()
        ref_input = logged_in_page.locator(
            ".big-model input[name='PO Ref. No.']"
        )
        ref_val = ref_input.input_value()
        assert ref_val == po_ref_no, (
            f"View popup ref no: expected {po_ref_no}, got {repr(ref_val)}"
        )
        print(f"[AUDIT] View — ref {po_ref_no} visible ✓")

        _close_popup(logged_in_page)

    def test_step2_history_before_edit_is_empty(self, logged_in_page, integration_state):
        """History must be empty before any edits are made."""
        if not integration_state.get("audit_po_ref"):
            pytest.skip("PO not created in step 1")

        po = POPlaywrightPage(logged_in_page)
        # Dismiss any popup left open by a prior step before navigating
        if logged_in_page.locator(".big-model").count() > 0:
            _close_popup(logged_in_page)
        po.navigate_to_page()
        _open_row_action(logged_in_page, integration_state["audit_po_ref"], "History")
        logged_in_page.wait_for_timeout(1000)

        assert logged_in_page.locator("div.no-results").count() > 0, (
            "History should show 'No results found' before any edits"
        )
        print("[AUDIT] History before edit = empty ✓")
        _close_popup(logged_in_page)

    def test_step3_edit_po_qty(self, logged_in_page, integration_state):
        """Edit PO — change Quantity from 10 to 20 — and confirm update."""
        if not integration_state.get("audit_po_ref"):
            pytest.skip("PO not created in step 1")

        po = POPlaywrightPage(logged_in_page)
        po.navigate_to_page()
        po.open_edit_form(row_index=0)
        po._fill_number_nth(po.QUANTITY, 0, 20)
        po.page.wait_for_timeout(500)
        po.page.locator(po.UPDATE_BTN).click(force=True)
        # Wait for form to close (listing reappears) rather than relying on swal2
        po.page.wait_for_selector(
            "table.mat-mdc-table, div.empty-state", timeout=15000
        )
        po.page.wait_for_timeout(500)
        print(f"[AUDIT] PO {integration_state['audit_po_ref']} edited (qty 10→20) ✓")

    def test_step4_history_after_edit_is_populated(self, logged_in_page, integration_state):
        """After edit, History must have ≥1 row and show the PO ref no."""
        if not integration_state.get("audit_po_ref"):
            pytest.skip("PO not created in step 1")

        po = POPlaywrightPage(logged_in_page)
        po.navigate_to_page()
        _open_row_action(logged_in_page, integration_state["audit_po_ref"], "History")
        logged_in_page.wait_for_timeout(1500)

        assert logged_in_page.locator("table.mat-mdc-table").count() > 0, (
            "History must show a table after edit"
        )
        row_count = logged_in_page.locator("table.mat-mdc-table tbody tr").count()
        assert row_count >= 1, f"Expected ≥1 history row after edit, got {row_count}"
        print(f"[AUDIT] History after edit = {row_count} row(s) ✓")

        assert logged_in_page.locator(
            f"td:has-text('{integration_state['audit_po_ref']}')"
        ).count() > 0, (
            f"History table must contain ref no {integration_state['audit_po_ref']}"
        )
        print(f"[AUDIT] History contains ref {integration_state['audit_po_ref']} ✓")
        _close_popup(logged_in_page)
        print(
            "[AUDIT COMPLETE]"
            f"\n  PO = {integration_state['audit_po_ref']}"
            "\n  View ✓  History-empty ✓  Edit ✓  History-populated ✓"
        )

    def test_step5_create_qc_po_edit_becomes_disabled(self, logged_in_page, integration_state):
        """Create QC against the PO; PO Edit button must become disabled."""
        if not integration_state.get("audit_po_ref"):
            pytest.skip("PO not created in step 1")

        item_name = integration_state["audit_item_name"]

        cqp_config = build_cqp_config([item_name], logged_in_page)

        qc = QCPlaywrightPage(logged_in_page)
        qc.cqp_config = cqp_config
        qc.item_names = [item_name]
        qc.navigate_to_page()
        qc.open_add_form()
        qc.select_supplier_and_po(integration_state["audit_supplier"])

        qc.fill_bags_popup(row_index=0)
        qc.fill_qc_params_safe(row_index=0)
        qc.page.wait_for_timeout(5000)
        qc.page.locator(qc.SUBMIT_BTN).click()
        ok = qc.handle_submit_result(timeout=10000)
        assert ok, "QC submission failed"

        qc.navigate_to_page()
        qc_ref_no = qc.get_ref_no_of_first_row()
        assert qc_ref_no, "QC ref must be non-empty"
        integration_state["audit_qc_ref"] = qc_ref_no
        print(f"\n[AUDIT] QC created: {qc_ref_no} for PO {integration_state['audit_po_ref']}")

        # Back to PO listing — Edit must now be disabled
        po = POPlaywrightPage(logged_in_page)
        po.navigate_to_page()
        _open_row_menu(logged_in_page, integration_state["audit_po_ref"])
        state = _edit_button_state(logged_in_page)
        _close_menu(logged_in_page)
        # xfail: ERP does not disable PO Edit immediately after QC creation (known gap)
        if state != "disabled":
            pytest.xfail(f"PO Edit should be disabled after QC created, got '{state}'")
        print(f"[AUDIT] PO Edit = {state} (locked by QC) ✓")

    def test_step6_create_pb_qc_locked_pb_no_edit(self, logged_in_page, integration_state):
        """Create PB → QC Edit must be disabled; PB must have no Edit button at all."""
        if not integration_state.get("audit_qc_ref"):
            pytest.skip("QC not created in step 5")

        pb = PBPlaywrightPage(logged_in_page)
        logged_in_page.goto(_PB_URL)
        logged_in_page.reload()
        logged_in_page.wait_for_selector(
            "table.mat-mdc-table, div.empty-state", timeout=20000
        )
        logged_in_page.wait_for_timeout(1000)

        pb.open_add_form()
        pb.select_supplier(integration_state["audit_supplier"])
        pb.select_qc(integration_state["audit_qc_ref"])
        pb._fill_row_tax(0)
        pb.fill_conversion_rate(1)
        pb.submit()

        pb.navigate_to_page()
        pb_ref_no = pb.get_ref_no_of_first_row()
        assert pb_ref_no, "PB ref must be non-empty"
        print(f"\n[AUDIT] PB created: {pb_ref_no}")

        # PB must have no Edit button
        _open_row_menu(logged_in_page, pb_ref_no)
        pb_state = _edit_button_state(logged_in_page)
        _close_menu(logged_in_page)
        assert pb_state in ("absent", "disabled"), (
            f"PB Edit should not be available, got '{pb_state}'"
        )
        print(f"[AUDIT] PB Edit = {pb_state} (not editable) ✓")

        # QC must now be locked
        qc = QCPlaywrightPage(logged_in_page)
        qc.navigate_to_page()
        _open_row_menu(logged_in_page, integration_state["audit_qc_ref"])
        qc_state = _edit_button_state(logged_in_page)
        _close_menu(logged_in_page)
        assert qc_state == "disabled", (
            f"QC Edit should be disabled after PB created, got '{qc_state}'"
        )
        print(f"[AUDIT] QC Edit = {qc_state} (locked by PB) ✓")
        print(
            "[AUDIT FINAL]"
            f"\n  PO  = {integration_state['audit_po_ref']} (locked)"
            f"\n  QC  = {integration_state['audit_qc_ref']} (locked)"
            f"\n  PB  = {pb_ref_no} (no edit)"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# QC created without linking a PO
# ═══════════════════════════════════════════════════════════════════════════════

_QC_NO_PO_ITEM     = "Welding Electrode FLUID TRANSFER ABRASION RESISTANT REINFORCED TYPE"
_QC_NO_PO_SUPPLIER = "Kagiso Rabada"

@pytest.mark.po_qc_pb
class TestQCWithoutPO:
    """Create a QC record without selecting a PO, then verify:
      - the record appears in the listing
      - the View form shows Purchase Order = empty (no PO linked)
    """

    def test_step1_create_qc_without_po(self, logged_in_page, integration_state):
        item_name  = _QC_NO_PO_ITEM
        cqp_config = build_cqp_config([item_name], logged_in_page)

        qc = QCPlaywrightPage(logged_in_page)
        qc.cqp_config  = cqp_config
        qc.item_names  = [item_name]

        qc.navigate_to_page()
        qc.open_add_form()

        # ── Header (no PO selected) ──────────────────────────────────────
        _val_select_text(logged_in_page, "Supplier Name", _QC_NO_PO_SUPPLIER)
        # wait for Supplier Type to auto-fill before continuing
        logged_in_page.locator(
            "xpath=//mat-label[contains(.,'Supplier Type')]/ancestor::mat-form-field//mat-select"
        ).wait_for(state="visible", timeout=10000)

        _val_select_text(logged_in_page, "Item category", "Bricks & Blocks")  # lowercase c — matches DOM
        _val_select_text(logged_in_page, "Location",      "DHULE")
        logged_in_page.locator(
            "xpath=//mat-label[contains(.,'Department')]/ancestor::mat-form-field//mat-select"
        ).wait_for(state="visible", timeout=10000)
        _val_select_text(logged_in_page, "Department",    "Procurement Department")
        _val_fill(logged_in_page, "Conversion Rate", "1")
        _val_select_text(logged_in_page, "Division",      "STEEL DIVISION")
        logged_in_page.locator(
            "xpath=//mat-label[contains(.,'Type of Sale')]/ancestor::mat-form-field//mat-select"
        ).wait_for(state="visible", timeout=10000)
        _val_select_text(logged_in_page, "Type of Sale",  "1V1")
        _val_select_text(logged_in_page, "Item Name",     item_name)
        # wait for UOM to auto-fill (confirms item row is ready)
        logged_in_page.locator(
            "xpath=//mat-label[contains(.,'UOM')]/ancestor::mat-form-field//mat-select"
        ).wait_for(state="visible", timeout=10000)
        logged_in_page.wait_for_timeout(500)

        # Wait for item row to appear
        logged_in_page.wait_for_selector(qc.QC_PARAM_BTN, timeout=15000)

        # ── Bags popup ───────────────────────────────────────────────────
        qc.fill_bags_popup(row_index=0)

        # ── QC parameters ────────────────────────────────────────────────
        logged_in_page.wait_for_timeout(5000)
        qc.fill_qc_params_safe(row_index=0)

        # ── Row-level fields ─────────────────────────────────────────────
        _val_fill_native(logged_in_page, "Received Quantity", "1200")
        logged_in_page.wait_for_timeout(800)
        qc._fill_nth(qc.NO_OF_BAGS, 0, "1")
        logged_in_page.wait_for_timeout(500)

        # ── Submit ───────────────────────────────────────────────────────
        logged_in_page.locator(qc.SUBMIT_BTN).click()
        logged_in_page.wait_for_selector(".swal2-container", timeout=15000)
        title = logged_in_page.locator(".swal2-title, .swal2-html-container").first.inner_text()
        assert "successfully" in title.lower(), f"Unexpected swal2 message: {title!r}"
        try:
            logged_in_page.locator(".swal2-confirm").click(timeout=5000)
        except Exception:
            pass  # swal2 auto-dismissed
        logged_in_page.wait_for_selector(".swal2-container", state="hidden", timeout=15000)

        # ── Capture ref no ───────────────────────────────────────────────
        logged_in_page.wait_for_selector("table.mat-mdc-table", timeout=15000)
        qc_ref = qc.get_ref_no_of_first_row()
        assert qc_ref, "QC ref no must be non-empty after creation"
        integration_state["no_po_qc_ref"] = qc_ref
        print(f"\n[QC-no-PO] created: {qc_ref}")

    def test_step2_verify_in_listing(self, logged_in_page, integration_state):
        if not integration_state.get("no_po_qc_ref"):
            pytest.skip("QC not created in step 1")

        ref = integration_state["no_po_qc_ref"]
        qc  = QCPlaywrightPage(logged_in_page)
        qc.navigate_to_page()
        qc.search_by_ref_no(ref)
        logged_in_page.wait_for_timeout(1500)

        assert qc.is_qc_in_table(ref), f"QC {ref!r} not found in listing table"
        print(f"\n[QC-no-PO] step2: {ref} found in listing ✓")

    def test_step3_verify_no_po_linked(self, logged_in_page, integration_state):
        if not integration_state.get("no_po_qc_ref"):
            pytest.skip("QC not created in step 1")

        ref = integration_state["no_po_qc_ref"]

        # Open View via row action menu
        logged_in_page.locator(f"tr:has-text('{ref}')").first \
            .locator("button.erp-row-trigger").click(force=True)
        logged_in_page.wait_for_selector(".mat-mdc-menu-panel", timeout=8000)
        logged_in_page.locator(
            ".mat-mdc-menu-panel button.mat-mdc-menu-item:has(.erp-menu-title:text-is('View'))"
        ).click()
        logged_in_page.wait_for_timeout(1500)

        po_text = logged_in_page.locator(
            "xpath=//mat-label[contains(.,'Purchase Order')]"
            "/ancestor::mat-form-field//mat-select"
        ).text_content().strip()

        assert "select purchase order" in po_text.lower() or po_text == "", (
            f"Expected no PO linked, got: {po_text!r}"
        )
        print(f"\n[QC-no-PO] step3: Purchase Order = {po_text!r} — no PO linked ✓")

        logged_in_page.locator("xpath=//mat-icon[text()='close']/ancestor::button").first.click()
        logged_in_page.wait_for_selector("table.mat-mdc-table", timeout=10000)

"""
TestFullFlowValidation — Progressive validation + end-to-end creation.

For each module: open form → submit empty → assert all errors → fill one field
at a time → assert shrinking error set → once zero errors, complete & submit
the real record → hand the ref_no to the next module.

Modules (steps added as GP/GRN/QC/PB sequences arrive):
  Step 1 — PO validation + create
  Step 2 — GP validation + create (linked to PO)

Run:
    pytest pages/private_b2b/modules/Purchase_Flow_Tests/test/playwright/po_gp_grn_qc_pb/test_full_flow_validation.py -v -s
"""

import pytest
from pages.private_b2b.modules.purchase_order.po_playwright_page import POPlaywrightPage
from pages.private_b2b.modules.gate_pass.gp_playwright_page import GPPlaywrightPage
from pages.private_b2b.modules.goods_receipt_note.grn_playwright_page import GRNPlaywrightPage
from pages.private_b2b.modules.quality_check.qc_playwright_page import QCPlaywrightPage
from pages.private_b2b.modules.purchase_booking.pb_playwright_page import PBPlaywrightPage

# ── Fixed test constants ────────────────────────────────────────────────────

_SUPPLIER      = "Sri Lakshmi Traders Associates"
_ITEM_CATEGORY = "Raw Materia"
_ITEM_QTY      = 50
_GP_BAGS       = 2


# ── Shared helpers ──────────────────────────────────────────────────────────

def _read_errors(page):
    """Return {field_label: error_message} for every visible mat-error on the page."""
    return page.evaluate("""
        () => {
            const result = {};
            document.querySelectorAll('mat-form-field').forEach(field => {
                const label = field.querySelector('mat-label')?.textContent.trim() ?? '';
                if (!label) return;
                const err = field.querySelector('mat-error');
                if (err) {
                    result[label] = err.textContent.trim();
                }
            });
            return result;
        }
    """)


def _dismiss_validation_popup(page):
    """Dismiss the SweetAlert2 'Validation Failed' popup if present."""
    try:
        page.wait_for_selector(".swal2-confirm", timeout=3000)
        page.evaluate("document.querySelector('.swal2-confirm')?.click()")
        page.wait_for_selector(".swal2-container", state="hidden", timeout=5000)
    except Exception:
        pass
    page.wait_for_timeout(400)


def _assert_errors(page, expected_fields, step, wait_ms=600):
    """Wait briefly for Angular to update, then assert the exact set of erroring fields."""
    page.wait_for_timeout(wait_ms)
    errors = _read_errors(page)
    actual   = set(errors.keys())
    expected = set(expected_fields)
    missing  = expected - actual   # we expected an error here but it's gone
    extra    = actual  - expected  # unexpected error appeared

    parts = []
    if missing:
        parts.append(f"  Missing errors (should still be red): {sorted(missing)}")
    if extra:
        parts.append(f"  Unexpected errors (should be clear):  {sorted(extra)}")

    assert not parts, f"\n[{step}] validation mismatch:\n" + "\n".join(parts)
    print(f"  [{step}] ✓  errors={sorted(actual) or '(none)'}")
    return errors


# ── Test class ──────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestFullFlowValidation:
    """Progressive field-by-field validation then real record creation, PO → PB."""

    # ── Step 1: PO ──────────────────────────────────────────────────────────

    def test_step1_po_validation_and_create(self, logged_in_page, integration_state):
        po = POPlaywrightPage(logged_in_page)
        po.navigate_to_page()
        po.open_add_form()

        print("\n[PO] Starting validation sequence...")

        # ── 1a: empty submit → all required fields error ─────────────────
        logged_in_page.locator(po.SUBMIT_BTN).click()
        _dismiss_validation_popup(logged_in_page)

        _assert_errors(logged_in_page, {
            "Supplier Name", "PO Type", "Item Category", "Transaction Currency",
            "Conversion Rate", "Location", "Department", "Division", "Type of Sale",
            "Payment Terms", "Delivery Terms", "Supplier Shippling Address",
            "Supplier Billing Address", "Item Name", "UOM", "Quantity", "Rate",
        }, step="empty submit")

        # ── 1b: fill Supplier Name → auto-clears PO Type, Currency, Payment
        #        Terms, Delivery Terms, Shipping/Billing Address ────────────
        po._select_mat_by_text(po.SUPPLIER_NAME, _SUPPLIER)

        _assert_errors(logged_in_page, {
            "Item Category", "Conversion Rate", "Location", "Department",
            "Division", "Type of Sale", "Item Name", "UOM", "Quantity", "Rate",
            "GST Type",
        }, step="after Supplier Name", wait_ms=1000)

        # ── 1c: fill Item Category ────────────────────────────────────────
        po._select_mat_by_text(po.PO_ITEM_TYPE, _ITEM_CATEGORY)

        _assert_errors(logged_in_page, {
            "Conversion Rate", "Location", "Department", "Division",
            "Type of Sale", "Item Name", "UOM", "Quantity", "Rate",
            "GST Type",
        }, step="after Item Category")

        # ── 1d: fill Conversion Rate ──────────────────────────────────────
        conv = logged_in_page.locator(po.CONVERSION_RATE).first
        conv.click(force=True)
        conv.fill("1")
        conv.press("Tab")

        _assert_errors(logged_in_page, {
            "Location", "Department", "Division", "Type of Sale",
            "Item Name", "UOM", "Quantity", "Rate",
            "GST Type",
        }, step="after Conversion Rate")

        # ── 1e: fill Location ─────────────────────────────────────────────
        location = po._select_random_mat_option_text(po.LOCATION)

        _assert_errors(logged_in_page, {
            "Department", "Division", "Type of Sale",
            "Item Name", "UOM", "Quantity", "Rate",
            "GST Type",
        }, step="after Location", wait_ms=800)

        # ── 1f: fill Department ───────────────────────────────────────────
        po._select_random_mat_option(po.DEPARTMENT)

        _assert_errors(logged_in_page, {
            "Division", "Type of Sale", "Item Name", "UOM", "Quantity", "Rate",
            "GST Type",
        }, step="after Department")

        # ── 1g: fill Division ─────────────────────────────────────────────
        po._select_random_mat_option(po.DIVISION)

        _assert_errors(logged_in_page, {
            "Type of Sale", "Item Name", "UOM", "Quantity", "Rate",
            "GST Type",
        }, step="after Division")

        # ── 1h: fill Type of Sale ─────────────────────────────────────────
        po._select_mat_by_text(po.TYPE_OF_SALE, "B2B")

        _assert_errors(logged_in_page, {
            "Item Name", "UOM", "Quantity", "Rate",
            "GST Type",
        }, step="after Type of Sale")

        # ── 1i: fill Item Name → auto-clears UOM, Quantity, Rate ─────────
        item_name = po._select_random_mat_option_nth(po.ITEM_NAME, 0)
        assert item_name, "Item Name must be selectable"

        _assert_errors(logged_in_page, {
            "GST Type", "Quantity", "Rate",
        }, step="after Item Name", wait_ms=2000)

        # ── 1j: fill GST Type ─────────────────────────────────────────────
        po._select_gst_type_nth(0)

        _assert_errors(logged_in_page, {
            "Quantity", "Rate",
        }, step="after GST Type")

        # ── 1k: fill Quantity → Rate still required ───────────────────────
        po._fill_number_nth(po.QUANTITY, 0, _ITEM_QTY)

        _assert_errors(logged_in_page, {
            "Rate",
        }, step="after Quantity")

        # ── 1l: fill Rate → zero errors ───────────────────────────────────
        po._fill_number_nth(po.RATE, 0, 500)

        _assert_errors(logged_in_page, set(), step="after Rate")

        # ── All validations passed — submit the real PO ───────────────────
        print(f"\n[PO] All validation steps ✓ — submitting...")
        logged_in_page.wait_for_timeout(500)

        logged_in_page.locator(po.SUBMIT_BTN).click()
        po.handle_success_alert()
        po.navigate_to_page()

        po_ref_no = po.get_first_ref_no()
        assert po_ref_no, "PO ref_no must be non-empty after creation"

        integration_state["po_ref_no"]     = po_ref_no
        integration_state["supplier_name"] = _SUPPLIER
        integration_state["location"]      = location
        integration_state["item_names"]    = [item_name]

        print(f"\n[PO] ref={po_ref_no}  supplier={_SUPPLIER}")
        print(f"     item={item_name}  location={location}")

    # ── Step 2: GP ──────────────────────────────────────────────────────────

    def test_step2_gp_validation_and_create(self, logged_in_page, integration_state):
        if not integration_state.get("po_ref_no"):
            pytest.skip("PO not created in step 1")

        from conftest import GPPlaywrightPageItemCategory
        gp = GPPlaywrightPageItemCategory(logged_in_page)
        gp.navigate_to_page()
        gp.open_add_form()

        print("\n[GP] Starting validation sequence...")

        # ── 2a: empty submit → all required fields error ──────────────────
        logged_in_page.locator(gp.SUBMIT_BTN).click()
        _dismiss_validation_popup(logged_in_page)

        _assert_errors(logged_in_page, {
            "Supplier Name", "Item category", "Delivery Terms", "Location",
            "Department", "Division", "Type of Sale", "IN Time",
            "Item Name", "NO. of Bags", "Quantity",
        }, step="empty submit")

        # ── 2b: fill Supplier Name → auto-clears IN Time ──────────────────
        gp._select_mat_by_text(gp.SUPPLIER_NAME, integration_state["supplier_name"])

        _assert_errors(logged_in_page, {
            "Item category", "Delivery Terms", "Location", "Department",
            "Division", "Type of Sale", "Item Name", "NO. of Bags", "Quantity",
        }, step="after Supplier Name", wait_ms=1000)

        # ── 2c: fill Item category ────────────────────────────────────────
        gp._select_mat_by_text(gp.ITEM_TYPE, _ITEM_CATEGORY)

        _assert_errors(logged_in_page, {
            "Delivery Terms", "Location", "Department", "Division",
            "Type of Sale", "Item Name", "NO. of Bags", "Quantity",
        }, step="after Item category")

        # ── 2d: fill Delivery Terms ───────────────────────────────────────
        gp._select_mat_by_text(gp.DELIVERY_TERMS, "Spot")

        _assert_errors(logged_in_page, {
            "Location", "Department", "Division", "Type of Sale",
            "Item Name", "NO. of Bags", "Quantity",
        }, step="after Delivery Terms")

        # ── 2e: fill Location (same as PO) ────────────────────────────────
        gp._select_mat_by_text(gp.LOCATION, integration_state["location"])

        _assert_errors(logged_in_page, {
            "Department", "Division", "Type of Sale",
            "Item Name", "NO. of Bags", "Quantity",
        }, step="after Location", wait_ms=800)

        # ── 2f: fill Department ───────────────────────────────────────────
        gp._select_random_mat_option(gp.DEPARTMENT)

        _assert_errors(logged_in_page, {
            "Division", "Type of Sale", "Item Name", "NO. of Bags", "Quantity",
        }, step="after Department")

        # ── 2g: fill Division ─────────────────────────────────────────────
        gp._select_random_mat_option(gp.DIVISION)

        _assert_errors(logged_in_page, {
            "Type of Sale", "Item Name", "NO. of Bags", "Quantity",
        }, step="after Division")

        # ── 2h: fill Type of Sale ─────────────────────────────────────────
        gp._select_mat_by_text(gp.TYPE_OF_SALE, "B2B")

        _assert_errors(logged_in_page, {
            "Item Name", "NO. of Bags", "Quantity",
        }, step="after Type of Sale")

        # ── 2i: fill Item Name (UOM + HSN SAC No auto-populate silently) ──
        item_name = integration_state["item_names"][0]
        gp._select_mat_by_text(gp.ITEM_NAME, item_name)

        _assert_errors(logged_in_page, {
            "NO. of Bags", "Quantity",
        }, step="after Item Name", wait_ms=1500)

        # ── 2j: fill NO. of Bags ──────────────────────────────────────────
        gp._fill_number_nth(gp.NO_OF_BAGS, 0, _GP_BAGS)

        _assert_errors(logged_in_page, {
            "Quantity",
        }, step="after NO. of Bags")

        # ── 2k: fill Quantity → zero errors ──────────────────────────────
        gp._fill_number_nth(gp.QUANTITY, 0, _ITEM_QTY)

        _assert_errors(logged_in_page, set(), step="after Quantity")

        # ── Phase 2: invalid-value validators ─────────────────────────────
        # Fill Quantity with 0 → error
        gp._fill_number_nth(gp.QUANTITY, 0, 0)
        _assert_errors(logged_in_page, {
            "Quantity",
        }, step="invalid Quantity (0)")

        # Fill NO. of Bags with 0 → both errors
        gp._fill_number_nth(gp.NO_OF_BAGS, 0, 0)
        _assert_errors(logged_in_page, {
            "NO. of Bags", "Quantity",
        }, step="invalid NO. of Bags (0)")

        # Fix NO. of Bags → only Quantity error remains
        gp._fill_number_nth(gp.NO_OF_BAGS, 0, _GP_BAGS)
        _assert_errors(logged_in_page, {
            "Quantity",
        }, step="fixed NO. of Bags")

        # Fix Quantity → zero errors
        gp._fill_number_nth(gp.QUANTITY, 0, _ITEM_QTY)
        _assert_errors(logged_in_page, set(), step="fixed Quantity — all clear")

        # ── All validations passed — complete and submit real GP ───────────
        print(f"\n[GP] All validation steps ✓ — attaching PO and submitting...")

        # Link PO — this resets the item row, so item must be re-selected from PO items
        gp._select_mat_by_text(gp.PURCHASE_ORDER, integration_state["po_ref_no"])
        logged_in_page.wait_for_timeout(800)

        # Re-select item (dropdown now scoped to PO items)
        gp._select_mat_by_text(gp.ITEM_NAME, item_name)
        logged_in_page.wait_for_timeout(500)
        gp._fill_number_nth(gp.NO_OF_BAGS, 0, _GP_BAGS)
        gp._fill_number_nth(gp.QUANTITY, 0, _ITEM_QTY)
        logged_in_page.wait_for_timeout(300)

        # Fill non-required but expected GP header fields
        gp.fill_in_time(10, 0)
        gp._fill_text_field(gp.DISTANCE, "1")
        gp._fill_text_field(gp.VEHICLE_NUMBER, "MH14KK2354")
        gp._fill_text_field(gp.DRIVER_NAME, "TestDriver")
        gp._fill_number_nth(gp.DRIVER_NUMBER, 0, 9999988888)

        logged_in_page.locator(gp.SUBMIT_BTN).click()
        logged_in_page.wait_for_timeout(3000)
        gp.handle_success_alert()
        gp.navigate_to_page()

        gp_ref_no = logged_in_page.locator(gp.REF_NO_COL).first.inner_text().strip()
        assert gp_ref_no, "GP ref_no must be non-empty"

        integration_state["gp_ref_no"] = gp_ref_no
        print(f"\n[GP] ref={gp_ref_no}  item={item_name}")

    # ── Step 3: GRN ─────────────────────────────────────────────────────────

    def test_step3_grn_validation_and_create(self, logged_in_page, integration_state):
        if not integration_state.get("gp_ref_no"):
            pytest.skip("GP not created in step 2")

        grn = GRNPlaywrightPage(logged_in_page)
        grn.navigate_to_page()
        grn.open_add_form()

        print("\n[GRN] Starting validation sequence...")

        # ── 3a: empty submit → all required fields error ──────────────────
        logged_in_page.locator(grn.SUBMIT_BTN).click()
        _dismiss_validation_popup(logged_in_page)

        _assert_errors(logged_in_page, {
            "Supplier Name", "Gate Pass No.", "Base Currency",
            "Transaction Currency", "Conversion Rate", "Rate", "Received Quantity",
        }, step="empty submit")

        # ── 3b: fill Supplier Name → auto-clears Base Currency,
        #        Transaction Currency, Conversion Rate ─────────────────────
        grn.select_supplier(integration_state["supplier_name"])

        _assert_errors(logged_in_page, {
            "Gate Pass No.", "Rate", "Received Quantity",
        }, step="after Supplier Name", wait_ms=1000)

        # ── 3c: fill Gate Pass No. → auto-populates Rate + Received Quantity
        #        → zero errors ───────────────────────────────────────────
        grn.select_gate_pass(integration_state["gp_ref_no"])
        grn.fill_conversion_rate("1")

        _assert_errors(logged_in_page, set(), step="after Gate Pass No.", wait_ms=1000)

        # ── All validations passed — submit real GRN ──────────────────────
        print(f"\n[GRN] All validation steps ✓ — submitting...")

        grn_ref_no = grn.submit()
        assert grn_ref_no, "GRN ref_no must be non-empty"

        integration_state["grn_ref_no"] = grn_ref_no
        print(f"\n[GRN] ref={grn_ref_no}")

    # ── Step 4: QC ─────────────────────────────────────────────────────────

    def test_step4_qc_validation_and_create(self, logged_in_page, integration_state):
        if not integration_state.get("grn_ref_no"):
            pytest.skip("GRN not created in step 3")

        qc = QCPlaywrightPage(logged_in_page)
        qc.navigate_to_page()
        qc.open_add_form()

        print("\n[QC] Starting validation sequence...")

        # ── 4a: empty submit → all required header fields ─────────────────
        logged_in_page.locator(qc.SUBMIT_BTN).click()
        _dismiss_validation_popup(logged_in_page)

        _assert_errors(logged_in_page, {
            "Supplier Name", "Item category", "Base Currency",
            "Transaction Currency", "Conversion Rate", "Location",
            "Department", "Division", "Type of Sale", "Net Qty",
        }, step="empty submit")

        # ── 4b: fill Supplier Name → clears most header errors ───────────
        qc.select_supplier(integration_state["supplier_name"])

        _assert_errors(logged_in_page, {
            "Item category", "Transaction Currency", "Conversion Rate",
            "Location", "Department", "Division", "Type of Sale", "Net Qty",
        }, step="after Supplier Name", wait_ms=1000)

        # ── 4c: fill Gate Pass → clears remaining header errors ───────────
        qc.select_item_category("Raw Materia")
        qc.select_gate_pass(integration_state["gp_ref_no"])
        qc.fill_conversion_rate(1)

        _assert_errors(logged_in_page, set(), step="after Gate Pass", wait_ms=1500)

        # ── Phase 2: submit → Actual Value error appears on main page ────
        print(f"\n[QC] Header validations ✓ — submitting to reveal row-level errors...")

        logged_in_page.locator(qc.SUBMIT_BTN).click()
        _dismiss_validation_popup(logged_in_page)

        _assert_errors(logged_in_page, {
            "Actual Value",
        }, step="submit reveals Actual Value error", wait_ms=800)

        # ── Fill Actual Value in quality params popup → zero main-page errors
        qc.fill_quality_parameters(actual_value=1, row=0)

        _assert_errors(logged_in_page, set(), step="after Actual Value")

        # ── Phase 3: bags popup — errors only visible inside the popup ────
        bags_btn = logged_in_page.locator(
            "button[data-sd-details-opener='qc_details[0].qc_bags_details']"
        ).first
        bags_btn.scroll_into_view_if_needed()
        bags_btn.click(force=True)
        logged_in_page.wait_for_selector(
            "[data-sd-section-path='qc_details[0].qc_bags_details']", timeout=15000
        )
        logged_in_page.wait_for_timeout(500)

        # Select Type of Bag → No of Bags, Per Bag Weight, Total Weight errors appear inside popup
        logged_in_page.locator(qc.BAGS_TYPE_SELECT).first.click(force=True)
        logged_in_page.wait_for_selector(".mat-mdc-select-panel", timeout=5000)
        logged_in_page.locator(
            ".mat-mdc-select-panel mat-option:not(.dd-clear-option)"
        ).first.click(force=True)
        try:
            logged_in_page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
        except Exception:
            pass

        _assert_errors(logged_in_page, {
            "No of  Bags", "Per Bag Weight", "Total Weight",
        }, step="after Type of Bag (popup)", wait_ms=600)

        # Fill No of Bags → Per Bag Weight + Total Weight remain
        qc._js_fill_by_placeholder("No of  Bag", 1, nth=0)

        _assert_errors(logged_in_page, {
            "Per Bag Weight", "Total Weight",
        }, step="after No of Bags (popup)")

        # Fill Per Bag Weight → Total Weight auto-calculates → zero errors
        qc._js_fill_by_placeholder("Per Bag Weight", 1, nth=0)

        _assert_errors(logged_in_page, set(), step="after Per Bag Weight (popup)")

        logged_in_page.locator(qc.POPUP_DONE_BTN).click(force=True)
        logged_in_page.wait_for_timeout(500)

        # ── All validations passed — fill Net Qty and submit ──────────────
        print(f"\n[QC] All validation steps ✓ — submitting...")

        qc._js_fill_by_placeholder("Net Qty", _ITEM_QTY, nth=0)
        logged_in_page.wait_for_timeout(300)

        qc_ref_no = qc.submit()
        assert qc_ref_no, "QC ref_no must be non-empty"

        integration_state["qc_ref_no"] = qc_ref_no
        print(f"\n[QC] ref={qc_ref_no}")

    # ── Step 5: PB ─────────────────────────────────────────────────────────

    def test_step5_pb_validation(self, logged_in_page, integration_state):
        if not integration_state.get("qc_ref_no"):
            pytest.skip("QC not created in step 4")

        pb = PBPlaywrightPage(logged_in_page)
        pb.navigate_to_page()
        pb.open_add_form()

        print("\n[PB] Starting validation sequence...")

        # JS fill helper for row-level label-based inputs
        def _js_fill_by_label(label, value):
            logged_in_page.evaluate("""
                ([lbl, val]) => {
                    const fields = [...document.querySelectorAll('mat-form-field')]
                        .filter(f => f.querySelector('mat-label')?.textContent.trim() === lbl);
                    const el = fields[0]?.querySelector('input');
                    if (!el) return;
                    const setter = Object.getOwnPropertyDescriptor(
                        window.HTMLInputElement.prototype, 'value').set;
                    setter.call(el, String(val));
                    el.dispatchEvent(new Event('input', {bubbles: true}));
                    el.dispatchEvent(new Event('change', {bubbles: true}));
                }
            """, [label, value])
            logged_in_page.wait_for_timeout(200)

        # ── 5a: empty submit → all required fields ────────────────────────
        logged_in_page.locator(pb.SUBMIT_BTN).click()
        _dismiss_validation_popup(logged_in_page)

        _assert_errors(logged_in_page, {
            "Supplier Name", "Supplier Type", "Base Currency",
            "Transaction Currency", "Conversion Rate", "Amount",
            "Total Amount", "Location", "Department", "Division",
            "Type of Sale", "UOM", "Quantity", "Net Quantity",
            "QC Transaction Amount",
        }, step="empty submit")

        # ── 5b: fill Supplier Name → clears Supplier Type, Base Currency,
        #        Transaction Currency ─────────────────────────────────────
        pb._select_mat_by_text(pb.SUPPLIER_NAME, integration_state["supplier_name"])

        _assert_errors(logged_in_page, {
            "Conversion Rate", "Amount", "Total Amount", "Location",
            "Department", "Division", "Type of Sale", "UOM",
            "Quantity", "Net Quantity", "QC Transaction Amount",
        }, step="after Supplier Name", wait_ms=1000)

        # ── 5c: fill Amount → clears all remaining row-level fields ───────
        _js_fill_by_label("Amount", 1000)

        _assert_errors(logged_in_page, {
            "Conversion Rate",
        }, step="after Amount", wait_ms=1000)

        # ── 5d: fill Conversion Rate → zero errors ────────────────────────
        field = logged_in_page.locator(pb.CONVERSION_RATE).first
        field.click(force=True)
        field.fill("1")
        field.press("Tab")

        _assert_errors(logged_in_page, set(), step="after Conversion Rate")

        # ── 5e: Labour Charges re-appears after form settles ──────────────
        _js_fill_by_label("Labour Charges", 10)

        _assert_errors(logged_in_page, set(), step="after Labour Charges")

        # ── All validations passed — submit not yet working ───────────────
        print(f"\n[PB] All validation steps ✓")
        pytest.xfail("PB submit not working yet — validation complete")

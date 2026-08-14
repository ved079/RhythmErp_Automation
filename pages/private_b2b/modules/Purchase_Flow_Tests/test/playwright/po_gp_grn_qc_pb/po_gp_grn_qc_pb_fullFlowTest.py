"""
Purchase Flow Full Test Suite — PO → GP → GRN → QC → PB

Classes:
  TestFullFlowValidation          — progressive field-by-field validation then create, PO → PB
  TestPO_GP_GRN_Multi_Item_Flow   — parallel E2E: 3-item PO → 4 GPs in 2 parallel pairs → PO Closed
  TestPO_GRN_QC_PB_Single_Item_Flow — sequential E2E: 1-item PO → GP1→GRN1→QC1 → GP2→GRN2→QC2 → PB1→PB2
  TestPO_GRN_QC_PB_Multi_Item_Single_GP — sequential E2E: 5-item PO → 1 GP → GRN → QC → PB
  TestPO_GRN_QC_PB_Multi_GP       — dynamic E2E: 5-item PO → random 2-5 GPs → each GP→GRN→QC→PB
  TestQCWeightToggle              — 7-9 item QC with alternating Weight/Rate toggle per row
  TestCalculationAssertions       — 1-item chain asserting QC Total Weight and PB Total Amount formulas

Parallel worker design (Multi_Item_Flow)
─────────────────────────────────────────
Each worker thread owns its entire Playwright stack (browser + login) because
Playwright's sync API ties Page objects to the OS thread that created them.
Submit sequencing uses threading.Event chains so no two GPs, GRNs, QCs, or PBs
ever hit the ERP backend simultaneously.

Calculation formulas
─────────────────────
QC Total Weight:
    Total Weight = No of Bags × Per Bag Weight   (auto-computed by Angular)

PB Total Amount:
    Total Amount = QC Transaction Amount + Tax amount − Labour Charges − Transport Charges
    - "Tax amount" (lowercase 'a') = IGST + CGST + SGST amounts combined
    - Discount is already baked into QC Transaction Amount at the QC stage;
      the Discount Rate field in PB is informational only — do NOT deduct again
    - Transport Charges is subtracted like Labour Charges
    - Round Off Debit/Credit omitted — negligible and not always present

Run individual class:
    pytest po_gp_grn_qc_pb_fullFlowTest.py::TestFullFlowValidation -v -s
    pytest po_gp_grn_qc_pb_fullFlowTest.py::TestCalculationAssertions -v -s
"""

import random
import threading
import traceback
import pytest
from pages.private_b2b.modules.purchase_order.po_playwright_page import POPlaywrightPage
from pages.private_b2b.modules.gate_pass.gp_playwright_page import GPPlaywrightPage
from pages.private_b2b.modules.goods_receipt_note.grn_playwright_page import GRNPlaywrightPage
from pages.private_b2b.modules.quality_check.qc_playwright_page import QCPlaywrightPage
from pages.private_b2b.modules.purchase_booking.pb_playwright_page import PBPlaywrightPage
from conftest import GPPlaywrightPageItemCategory


# ══════════════════════════════════════════════════════════════════════════════
# Shared module-level helpers
# ══════════════════════════════════════════════════════════════════════════════

def _read_errors(page):
    """Return {field_label: error_message} for every visible mat-error on the page."""
    return page.evaluate("""
        () => {
            const result = {};
            document.querySelectorAll('mat-form-field').forEach(field => {
                const label = field.querySelector('mat-label')?.textContent.trim() ?? '';
                if (!label) return;
                const err = field.querySelector('mat-error');
                if (err) { result[label] = err.textContent.trim(); }
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
    errors   = _read_errors(page)
    actual   = set(errors.keys())
    expected = set(expected_fields)
    missing  = expected - actual
    extra    = actual  - expected

    parts = []
    if missing:
        parts.append(f"  Missing errors (should still be red): {sorted(missing)}")
    if extra:
        parts.append(f"  Unexpected errors (should be clear):  {sorted(extra)}")

    assert not parts, f"\n[{step}] validation mismatch:\n" + "\n".join(parts)
    print(f"  [{step}] ✓  errors={sorted(actual) or '(none)'}")
    return errors


def _js_read_num_by_label(page, label_text: str, nth: int = 0):
    """Read the numeric value of the nth input whose mat-label exactly matches label_text."""
    return page.evaluate(
        """
        ([label, nth]) => {
            const fields = [...document.querySelectorAll('mat-form-field')].filter(f =>
                f.querySelector('mat-label')?.textContent.trim() === label
            );
            const el = fields[nth]?.querySelector('input');
            return el ? parseFloat(el.value.replace(/,/g, '')) : null;
        }
        """,
        [label_text, nth],
    )


# ══════════════════════════════════════════════════════════════════════════════
# TestFullFlowValidation
# ══════════════════════════════════════════════════════════════════════════════

_SUPPLIER      = "Sri Lakshmi Traders Associates"
_ITEM_CATEGORY = "Raw Materia"
_ITEM_QTY      = 50
_GP_BAGS       = 2


@pytest.mark.integration
class TestFullFlowValidation:
    """Progressive field-by-field validation then real record creation, PO → PB."""

    # ── Step 1: PO ──────────────────────────────────────────────────────────

    def test_step1_po_validation_and_create(self, logged_in_page, integration_state):
        po = POPlaywrightPage(logged_in_page)
        po.navigate_to_page()
        po.open_add_form()

        print("\n[PO] Starting validation sequence...")

        logged_in_page.locator(po.SUBMIT_BTN).click()
        _dismiss_validation_popup(logged_in_page)

        _assert_errors(logged_in_page, {
            "Supplier Name", "PO Type", "Item Category", "Transaction Currency",
            "Conversion Rate", "Location", "Department", "Division", "Type of Sale",
            "Payment Terms", "Delivery Terms", "Supplier Shippling Address",
            "Supplier Billing Address", "Item Name", "UOM", "Quantity", "Rate",
        }, step="empty submit")

        po._select_mat_by_text(po.SUPPLIER_NAME, _SUPPLIER)
        _assert_errors(logged_in_page, {
            "Item Category", "Conversion Rate", "Location", "Department",
            "Division", "Type of Sale", "Item Name", "UOM", "Quantity", "Rate",
            "GST Type",
        }, step="after Supplier Name", wait_ms=1000)

        po._select_mat_by_text(po.PO_ITEM_TYPE, _ITEM_CATEGORY)
        _assert_errors(logged_in_page, {
            "Conversion Rate", "Location", "Department", "Division",
            "Type of Sale", "Item Name", "UOM", "Quantity", "Rate",
            "GST Type",
        }, step="after Item Category")

        conv = logged_in_page.locator(po.CONVERSION_RATE).first
        conv.click(force=True)
        conv.fill("1")
        conv.press("Tab")
        _assert_errors(logged_in_page, {
            "Location", "Department", "Division", "Type of Sale",
            "Item Name", "UOM", "Quantity", "Rate",
            "GST Type",
        }, step="after Conversion Rate")

        location = po._select_random_mat_option_text(po.LOCATION)
        _assert_errors(logged_in_page, {
            "Department", "Division", "Type of Sale",
            "Item Name", "UOM", "Quantity", "Rate",
            "GST Type",
        }, step="after Location", wait_ms=800)

        po._select_random_mat_option(po.DEPARTMENT)
        _assert_errors(logged_in_page, {
            "Division", "Type of Sale", "Item Name", "UOM", "Quantity", "Rate",
            "GST Type",
        }, step="after Department")

        po._select_random_mat_option(po.DIVISION)
        _assert_errors(logged_in_page, {
            "Type of Sale", "Item Name", "UOM", "Quantity", "Rate",
            "GST Type",
        }, step="after Division")

        po._select_mat_by_text(po.TYPE_OF_SALE, "B2B")
        _assert_errors(logged_in_page, {
            "Item Name", "UOM", "Quantity", "Rate",
            "GST Type",
        }, step="after Type of Sale")

        item_name = po._select_random_mat_option_nth(po.ITEM_NAME, 0)
        assert item_name, "Item Name must be selectable"
        _assert_errors(logged_in_page, {
            "GST Type", "Quantity", "Rate",
        }, step="after Item Name", wait_ms=2000)

        po._select_gst_type_nth(0)
        _assert_errors(logged_in_page, {
            "Quantity", "Rate",
        }, step="after GST Type")

        po._fill_number_nth(po.QUANTITY, 0, _ITEM_QTY)
        _assert_errors(logged_in_page, {"Rate"}, step="after Quantity")

        po._fill_number_nth(po.RATE, 0, 500)
        _assert_errors(logged_in_page, set(), step="after Rate")

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

        gp = GPPlaywrightPageItemCategory(logged_in_page)
        gp.navigate_to_page()
        gp.open_add_form()

        print("\n[GP] Starting validation sequence...")

        logged_in_page.locator(gp.SUBMIT_BTN).click()
        _dismiss_validation_popup(logged_in_page)

        _assert_errors(logged_in_page, {
            "Supplier Name", "Item category", "Delivery Terms", "Location",
            "Department", "Division", "Type of Sale", "IN Time",
            "Item Name", "NO. of Bags", "Quantity",
        }, step="empty submit")

        gp._select_mat_by_text(gp.SUPPLIER_NAME, integration_state["supplier_name"])
        _assert_errors(logged_in_page, {
            "Item category", "Delivery Terms", "Location", "Department",
            "Division", "Type of Sale", "Item Name", "NO. of Bags", "Quantity",
        }, step="after Supplier Name", wait_ms=1000)

        gp._select_mat_by_text(gp.ITEM_TYPE, _ITEM_CATEGORY)
        _assert_errors(logged_in_page, {
            "Delivery Terms", "Location", "Department", "Division",
            "Type of Sale", "Item Name", "NO. of Bags", "Quantity",
        }, step="after Item category")

        gp._select_mat_by_text(gp.DELIVERY_TERMS, "Spot")
        _assert_errors(logged_in_page, {
            "Location", "Department", "Division", "Type of Sale",
            "Item Name", "NO. of Bags", "Quantity",
        }, step="after Delivery Terms")

        gp._select_mat_by_text(gp.LOCATION, integration_state["location"])
        _assert_errors(logged_in_page, {
            "Department", "Division", "Type of Sale",
            "Item Name", "NO. of Bags", "Quantity",
        }, step="after Location", wait_ms=800)

        gp._select_random_mat_option(gp.DEPARTMENT)
        _assert_errors(logged_in_page, {
            "Division", "Type of Sale", "Item Name", "NO. of Bags", "Quantity",
        }, step="after Department")

        gp._select_random_mat_option(gp.DIVISION)
        _assert_errors(logged_in_page, {
            "Type of Sale", "Item Name", "NO. of Bags", "Quantity",
        }, step="after Division")

        gp._select_mat_by_text(gp.TYPE_OF_SALE, "B2B")
        _assert_errors(logged_in_page, {
            "Item Name", "NO. of Bags", "Quantity",
        }, step="after Type of Sale")

        item_name = integration_state["item_names"][0]
        gp._select_mat_by_text(gp.ITEM_NAME, item_name)
        _assert_errors(logged_in_page, {
            "NO. of Bags", "Quantity",
        }, step="after Item Name", wait_ms=1500)

        gp._fill_number_nth(gp.NO_OF_BAGS, 0, _GP_BAGS)
        _assert_errors(logged_in_page, {"Quantity"}, step="after NO. of Bags")

        gp._fill_number_nth(gp.QUANTITY, 0, _ITEM_QTY)
        _assert_errors(logged_in_page, set(), step="after Quantity")

        # Invalid-value validators
        gp._fill_number_nth(gp.QUANTITY, 0, 0)
        _assert_errors(logged_in_page, {"Quantity"}, step="invalid Quantity (0)")

        gp._fill_number_nth(gp.NO_OF_BAGS, 0, 0)
        _assert_errors(logged_in_page, {"NO. of Bags", "Quantity"}, step="invalid NO. of Bags (0)")

        gp._fill_number_nth(gp.NO_OF_BAGS, 0, _GP_BAGS)
        _assert_errors(logged_in_page, {"Quantity"}, step="fixed NO. of Bags")

        gp._fill_number_nth(gp.QUANTITY, 0, _ITEM_QTY)
        _assert_errors(logged_in_page, set(), step="fixed Quantity — all clear")

        print(f"\n[GP] All validation steps ✓ — attaching PO and submitting...")

        gp._select_mat_by_text(gp.PURCHASE_ORDER, integration_state["po_ref_no"])
        logged_in_page.wait_for_timeout(800)
        gp._select_mat_by_text(gp.ITEM_NAME, item_name)
        logged_in_page.wait_for_timeout(500)
        gp._fill_number_nth(gp.NO_OF_BAGS, 0, _GP_BAGS)
        gp._fill_number_nth(gp.QUANTITY, 0, _ITEM_QTY)
        logged_in_page.wait_for_timeout(300)

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

        logged_in_page.locator(grn.SUBMIT_BTN).click()
        _dismiss_validation_popup(logged_in_page)

        _assert_errors(logged_in_page, {
            "Supplier Name", "Gate Pass No.", "Base Currency",
            "Transaction Currency", "Conversion Rate", "Rate", "Received Quantity",
        }, step="empty submit")

        grn.select_supplier(integration_state["supplier_name"])
        _assert_errors(logged_in_page, {
            "Gate Pass No.", "Rate", "Received Quantity",
        }, step="after Supplier Name", wait_ms=1000)

        grn.select_gate_pass(integration_state["gp_ref_no"])
        grn.fill_conversion_rate("1")
        _assert_errors(logged_in_page, set(), step="after Gate Pass No.", wait_ms=1000)

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

        logged_in_page.locator(qc.SUBMIT_BTN).click()
        _dismiss_validation_popup(logged_in_page)

        _assert_errors(logged_in_page, {
            "Supplier Name", "Item category", "Base Currency",
            "Transaction Currency", "Conversion Rate", "Location",
            "Department", "Division", "Type of Sale", "Net Qty",
        }, step="empty submit")

        qc.select_supplier(integration_state["supplier_name"])
        _assert_errors(logged_in_page, {
            "Item category", "Transaction Currency", "Conversion Rate",
            "Location", "Department", "Division", "Type of Sale", "Net Qty",
        }, step="after Supplier Name", wait_ms=1000)

        qc.select_item_category("Raw Materia")
        _assert_errors(logged_in_page, {
            "Transaction Currency", "Conversion Rate", "Location",
            "Department", "Division", "Type of Sale", "Net Qty",
        }, step="after Item category", wait_ms=1500)

        qc.select_gate_pass(integration_state["gp_ref_no"])
        _assert_errors(logged_in_page, {"Conversion Rate"}, step="after Gate Pass", wait_ms=1500)

        qc.fill_conversion_rate(1)
        _assert_errors(logged_in_page, set(), step="after Conversion Rate")

        print(f"\n[QC] Header validations ✓ — submitting to reveal bag-level errors...")

        logged_in_page.locator(qc.SUBMIT_BTN).click()
        _dismiss_validation_popup(logged_in_page)

        bags_btn = logged_in_page.locator(
            "button[data-sd-details-opener='qc_details[0].qc_bags_details']"
        ).first
        bags_btn.scroll_into_view_if_needed()
        bags_btn.click(force=True)
        logged_in_page.wait_for_selector(
            "[data-sd-section-path='qc_details[0].qc_bags_details']", timeout=15000
        )
        logged_in_page.wait_for_timeout(500)

        _assert_errors(logged_in_page, {
            "Type of Bag", "No of  Bags", "Per Bag Weight", "Total Weight",
        }, step="bags popup opened", wait_ms=800)

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
        }, step="after Type of Bag")

        qc._js_fill_by_placeholder("No of  Bag", 1, nth=0)
        _assert_errors(logged_in_page, {
            "Per Bag Weight", "Total Weight",
        }, step="after No of Bags")

        _QC_BAGS = 1
        _QC_PER_BAG_WEIGHT = 1.0
        qc._js_fill_by_placeholder("Per Bag Weight", _QC_PER_BAG_WEIGHT, nth=0)
        _assert_errors(logged_in_page, set(), step="after Per Bag Weight")

        logged_in_page.wait_for_timeout(400)
        total_weight = logged_in_page.evaluate("""
            () => {
                const fields = [...document.querySelectorAll('mat-form-field')]
                    .filter(f => f.querySelector('mat-label')?.textContent.trim() === 'Total Weight');
                const el = fields[0]?.querySelector('input');
                return el ? parseFloat(el.value) : null;
            }
        """)
        expected_tw = round(_QC_BAGS * _QC_PER_BAG_WEIGHT, 4)
        assert total_weight is not None and abs(total_weight - expected_tw) < 0.01, (
            f"Total Weight: expected {expected_tw} ({_QC_BAGS} bags × {_QC_PER_BAG_WEIGHT} kg), got {total_weight}"
        )
        print(f"  [Total Weight] ✓  {_QC_BAGS} × {_QC_PER_BAG_WEIGHT} = {total_weight}")

        logged_in_page.locator(qc.POPUP_DONE_BTN).click(force=True)
        logged_in_page.wait_for_timeout(500)

        qc.fill_quality_parameters(actual_value=1, row=0)
        _assert_errors(logged_in_page, set(), step="after Actual Value")

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

        def _read_num_by_label(label, nth=0):
            return logged_in_page.evaluate("""
                ([lbl, idx]) => {
                    const fields = [...document.querySelectorAll('mat-form-field')]
                        .filter(f => f.querySelector('mat-label')?.textContent.trim() === lbl);
                    const el = fields[idx]?.querySelector('input');
                    return el ? (parseFloat(el.value) || 0) : 0;
                }
            """, [label, nth])

        logged_in_page.locator(pb.SUBMIT_BTN).click()
        _dismiss_validation_popup(logged_in_page)

        _assert_errors(logged_in_page, {
            "Supplier Name", "Supplier Type", "Base Currency",
            "Transaction Currency", "Conversion Rate", "Amount",
            "Total Amount", "Location", "Department", "Division",
            "Type of Sale", "Quantity", "Net Quantity",
            "QC Transaction Amount",
        }, step="empty submit")

        pb._select_mat_by_text(pb.SUPPLIER_NAME, integration_state["supplier_name"])
        _assert_errors(logged_in_page, {
            "Conversion Rate", "Amount", "Total Amount", "Location",
            "Department", "Division", "Type of Sale",
            "Quantity", "Net Quantity", "QC Transaction Amount",
        }, step="after Supplier Name", wait_ms=1000)

        field = logged_in_page.locator(pb.CONVERSION_RATE).first
        field.click(force=True)
        field.fill("1")
        field.press("Tab")
        _assert_errors(logged_in_page, {
            "Amount", "Total Amount", "Location", "Department", "Division",
            "Type of Sale", "Quantity", "Net Quantity", "QC Transaction Amount",
        }, step="after Conversion Rate", wait_ms=800)

        pb.select_qc(integration_state["qc_ref_no"])
        _assert_errors(logged_in_page, set(), step="after QC selected", wait_ms=1500)

        logged_in_page.wait_for_timeout(500)
        pb_amount = _read_num_by_label("Amount")
        print(f"  [PB] auto-populated Amount = {pb_amount}")

        # Negative Labour Charges → validation error
        pb.fill_row(0)
        logged_in_page.evaluate("""
            () => {
                const fields = [...document.querySelectorAll('mat-form-field')]
                    .filter(f => f.querySelector('mat-label')?.textContent.trim() === 'Labour Charges');
                const el = fields[0]?.querySelector('input');
                if (!el) return;
                const setter = Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype, 'value').set;
                setter.call(el, '-1');
                el.dispatchEvent(new Event('input', {bubbles: true}));
                el.dispatchEvent(new Event('change', {bubbles: true}));
            }
        """)
        logged_in_page.wait_for_timeout(300)
        logged_in_page.locator(pb.SUBMIT_BTN).click()
        _dismiss_validation_popup(logged_in_page)
        _assert_errors(logged_in_page, {"Labour Charges"}, step="negative Labour Charges", wait_ms=600)

        # Fix Labour to known value then assert Total Amount formula
        _FIXED_LABOUR = 10.0
        logged_in_page.evaluate("""
            ([val]) => {
                const fields = [...document.querySelectorAll('mat-form-field')]
                    .filter(f => f.querySelector('mat-label')?.textContent.trim() === 'Labour Charges');
                const el = fields[0]?.querySelector('input');
                if (!el) return;
                const setter = Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype, 'value').set;
                setter.call(el, String(val));
                el.dispatchEvent(new Event('input', {bubbles: true}));
                el.dispatchEvent(new Event('change', {bubbles: true}));
            }
        """, [_FIXED_LABOUR])
        logged_in_page.wait_for_timeout(800)

        # Formula: Total = QC Transaction Amount + Tax amount − Labour
        # Discount is baked into QC Transaction Amount; do NOT deduct again.
        gst_amount   = _read_num_by_label("Tax amount")
        expected_total = round(pb_amount + gst_amount - _FIXED_LABOUR, 2)
        actual_total   = _read_num_by_label("Total Amount")

        print(
            f"  [PB Total] Amount={pb_amount}  GST={gst_amount}  Labour={_FIXED_LABOUR}"
            f"  → expected={expected_total}  actual={actual_total}"
        )
        assert abs(expected_total - actual_total) < 1.0, (
            f"PB Total Amount mismatch: expected {expected_total}, got {actual_total}"
        )

        print(f"\n[PB] All validation steps ✓ — submitting...")
        pb_ref_no = pb.submit()
        assert pb_ref_no, "PB ref_no must be non-empty"
        integration_state["pb_ref_no"] = pb_ref_no
        print(f"\n[PB] ref={pb_ref_no}")


# ══════════════════════════════════════════════════════════════════════════════
# Parallel E2E helpers (used by TestPO_GP_GRN_Multi_Item_Flow)
# ══════════════════════════════════════════════════════════════════════════════

_LOGIN_URL = "https://rhythmerp.algorhythms.in"
_EMAIL     = "kedar@rhythmflows.com"
_PASSWORD  = "kedar@rhythmflows.com"
_TENANT    = "Agristack Company ltd"

PO_QTY  = 200
GP1_QTY = 120
GP2_QTY = PO_QTY - GP1_QTY

MI_QTY_A = 25
MI_QTY_B = 20
MI_QTY_C = 15


def _create_grn(grn_page, supplier_name, gp_ref_no, po_ref_no,
                expected_gp_qty, expected_rate):
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
    from playwright.sync_api import sync_playwright
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False, slow_mo=150)
            page = browser.new_page(viewport={"width": 1372, "height": 625})
            _login(page, login_url, email, password, tenant)

            gp = GPPlaywrightPageItemCategory(page)
            gp.navigate_to_page()
            gp.fill_items_form(supplier_name, items, location=location, type_of_sale="B2B", po_ref_no=po_ref_no)

            if wait_for_event is not None:
                wait_for_event.wait()

            gp_ref, row_dicts = gp.submit_items_form(items)
            if gp_done_event is not None:
                gp_done_event.set()

            grn = GRNPlaywrightPage(page)
            grn.navigate_to_page()
            grn.open_add_form()
            grn.select_supplier(supplier_name)
            grn.select_gate_pass(gp_ref)

            actual_gp_qtys = [grn.read_gate_pass_qty_nth(i) for i in range(len(items))]
            for i, (_, _, qty) in enumerate(items):
                grn.fill_accepted_qty_nth(i, int(qty))

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


def _run_parallel_pair(supplier, location, po_ref_no,
                       items_a, items_b, label_a, label_b, tenant=""):
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
        name=label_a,
    )
    t_b = threading.Thread(
        target=_gp_grn_worker,
        args=(_LOGIN_URL, _EMAIL, _PASSWORD,
              supplier, items_b, location, po_ref_no,
              results, errors, label_b, tenant),
        kwargs={"wait_for_event": gp_done, "wait_for_grn_event": grn_done},
        name=label_b,
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


# ══════════════════════════════════════════════════════════════════════════════
# TestPO_GP_GRN_Multi_Item_Flow
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestPO_GP_GRN_Multi_Item_Flow:
    """Multi-item parallel E2E: 3-item PO → 4 GPs in 2 parallel pairs → PO Closed.

    Pair 1: GP1(A=10) ‖ GP2(B=10,C=8)
    Pair 2: GP3(A=15,B=5) ‖ GP4(B=5,C=7)
    """

    def test_step1_create_po(self, po_page, integration_state):
        total, row_dicts, supplier_name, location, po_ref_no = \
            po_page.create_record_for_integration(
                item_configs=[(MI_QTY_A, 0, 0), (MI_QTY_B, 0, 0), (MI_QTY_C, 0, 0)],
                forced_location="Pune",
            )

        assert po_ref_no,          "PO ref_no must be non-empty"
        assert len(row_dicts) == 3, f"Expected 3 PO rows, got {len(row_dicts)}"

        integration_state.update({
            "po_ref_no":  po_ref_no,
            "supplier":   supplier_name,
            "location":   location,
            "item_a":     row_dicts[0]["item_name"],
            "item_b":     row_dicts[1]["item_name"],
            "item_c":     row_dicts[2]["item_name"],
            "rates":      {rd["item_name"]: rd["rate"] for rd in row_dicts},
        })
        print(
            f"\n[PO] ref={po_ref_no}  supplier={supplier_name}  location={location}"
            f"\n  A={row_dicts[0]['item_name']} qty={MI_QTY_A}"
            f"\n  B={row_dicts[1]['item_name']} qty={MI_QTY_B}"
            f"\n  C={row_dicts[2]['item_name']} qty={MI_QTY_C}"
        )

    def test_step2_pair1_parallel(self, integration_state):
        if not integration_state.get("po_ref_no"):
            pytest.skip("PO not created in step 1")

        supplier  = integration_state["supplier"]
        location  = integration_state["location"]
        po_ref_no = integration_state["po_ref_no"]
        item_a, item_b, item_c = integration_state["item_a"], integration_state["item_b"], integration_state["item_c"]

        results = _run_parallel_pair(
            supplier, location, po_ref_no,
            [(item_a, 2, 10)], [(item_b, 3, 10), (item_c, 2, 8)],
            "gp1_grn1", "gp2_grn2", _TENANT,
        )
        _assert_pair_results(results, "gp1_grn1", "gp2_grn2")
        _print_pair(results, "gp1_grn1", "gp2_grn2", pair_num=1)
        integration_state["pair1_results"] = results

    def test_step3_pair2_parallel(self, integration_state):
        if not integration_state.get("pair1_results"):
            pytest.skip("Pair 1 did not complete")

        supplier  = integration_state["supplier"]
        location  = integration_state["location"]
        po_ref_no = integration_state["po_ref_no"]
        item_a, item_b, item_c = integration_state["item_a"], integration_state["item_b"], integration_state["item_c"]

        results = _run_parallel_pair(
            supplier, location, po_ref_no,
            [(item_a, 3, 15), (item_b, 1, 5)], [(item_b, 1, 5), (item_c, 2, 7)],
            "gp3_grn3", "gp4_grn4", _TENANT,
        )
        _assert_pair_results(results, "gp3_grn3", "gp4_grn4")
        _print_pair(results, "gp3_grn3", "gp4_grn4", pair_num=2)
        integration_state["pair2_results"] = results

    def test_step4_verify_po_closed(self, po_page, integration_state):
        if not integration_state.get("pair2_results"):
            pytest.skip("Pair 2 did not complete")

        po_ref_no = integration_state["po_ref_no"]
        po_page.navigate_to_page()
        po_page.trigger_po_status_recalculation()
        closed = po_page.is_po_closed(po_ref_no)
        assert closed, f"PO {po_ref_no} should be 'Closed' after all items fully received"

        p1 = integration_state["pair1_results"]
        p2 = integration_state["pair2_results"]
        print(
            f"\n[MULTI-ITEM PARALLEL CYCLE COMPLETE]"
            f"\n  PO = {po_ref_no}  (Closed ✓)"
            f"\n  Pair 1 → GP={p1['gp1_grn1']['gp_ref']} GRN={p1['gp1_grn1']['grn_ref']}"
            f"         ‖ GP={p1['gp2_grn2']['gp_ref']} GRN={p1['gp2_grn2']['grn_ref']}"
            f"\n  Pair 2 → GP={p2['gp3_grn3']['gp_ref']} GRN={p2['gp3_grn3']['grn_ref']}"
            f"         ‖ GP={p2['gp4_grn4']['gp_ref']} GRN={p2['gp4_grn4']['grn_ref']}"
        )


# ══════════════════════════════════════════════════════════════════════════════
# TestPO_GRN_QC_PB_Single_Item_Flow
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestPO_GRN_QC_PB_Single_Item_Flow:
    """Sequential E2E: 1-item PO → GP1→GRN1→QC1 → GP2→GRN2→QC2 → PB1→PB2."""

    def test_step1_create_po(self, po_page, integration_state):
        total, row_dicts, supplier_name, location, po_ref_no = \
            po_page.create_record_for_integration(item_configs=[(PO_QTY, 0, 0)])

        assert po_ref_no and row_dicts and supplier_name
        integration_state.update({
            "po_ref_no":     po_ref_no,
            "supplier_name": supplier_name,
            "location":      location,
            "item_name":     row_dicts[0]["item_name"],
            "rate":          row_dicts[0]["rate"],
        })
        print(f"\n[PO] ref={po_ref_no}  item={row_dicts[0]['item_name']}  qty={PO_QTY}")

    def test_step2_create_gp1(self, gp_page, integration_state):
        if not integration_state.get("po_ref_no"):
            pytest.skip("PO not created in step 1")

        gp_ref_no, _ = gp_page.create_record_with_specific_item(
            supplier_name=integration_state["supplier_name"],
            item_name=integration_state["item_name"],
            bags=3, qty=GP1_QTY,
            location=integration_state["location"],
            type_of_sale="B2B",
            po_ref_no=integration_state["po_ref_no"],
        )
        assert gp_ref_no
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
        assert grn_ref_no
        integration_state["grn1_ref_no"] = grn_ref_no
        print(f"\n[GRN1] ref={grn_ref_no}")

    def test_step4_qc1(self, qc_page, integration_state):
        if not integration_state.get("grn1_ref_no"):
            pytest.skip("GRN1 not created in step 3")

        qc_ref_no = qc_page.create_for_integration(
            supplier_name=integration_state["supplier_name"],
            gp_ref_no=integration_state["gp1_ref_no"],
            accepted_qty=GP1_QTY,
        )
        assert qc_ref_no
        integration_state["qc1_ref_no"] = qc_ref_no
        print(f"\n[QC1] ref={qc_ref_no}")

    def test_step5_create_gp2(self, gp_page_tab2, integration_state):
        if not integration_state.get("qc1_ref_no"):
            pytest.skip("QC1 not created in step 4")

        gp_ref_no, _ = gp_page_tab2.create_record_with_specific_item(
            supplier_name=integration_state["supplier_name"],
            item_name=integration_state["item_name"],
            bags=2, qty=GP2_QTY,
            location=integration_state["location"],
            type_of_sale="B2B",
            po_ref_no=integration_state["po_ref_no"],
        )
        assert gp_ref_no
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
        assert grn_ref_no
        integration_state["grn2_ref_no"] = grn_ref_no
        print(f"\n[GRN2] ref={grn_ref_no}")

    def test_step7_qc2(self, qc_page, integration_state):
        if not integration_state.get("grn2_ref_no"):
            pytest.skip("GRN2 not created in step 6")

        qc_ref_no = qc_page.create_for_integration(
            supplier_name=integration_state["supplier_name"],
            gp_ref_no=integration_state["gp2_ref_no"],
            accepted_qty=GP2_QTY,
        )
        assert qc_ref_no
        integration_state["qc2_ref_no"] = qc_ref_no
        print(f"\n[QC2] ref={qc_ref_no}")

    def test_step8_create_pb1(self, pb_page, integration_state):
        if not integration_state.get("qc2_ref_no"):
            pytest.skip("QC2 not created in step 7")

        pb_ref_no = pb_page.create_for_integration(
            supplier_name=integration_state["supplier_name"],
            qc_ref_no=integration_state["qc1_ref_no"],
        )
        assert pb_ref_no
        integration_state["pb1_ref_no"] = pb_ref_no
        print(f"\n[PB1] ref={pb_ref_no}")

    def test_step9_create_pb2(self, pb_page, integration_state):
        if not integration_state.get("pb1_ref_no"):
            pytest.skip("PB1 not created in step 8")

        pb_ref_no = pb_page.create_for_integration(
            supplier_name=integration_state["supplier_name"],
            qc_ref_no=integration_state["qc2_ref_no"],
        )
        assert pb_ref_no
        integration_state["pb2_ref_no"] = pb_ref_no
        print(f"\n[PB2] ref={pb_ref_no}")


# ══════════════════════════════════════════════════════════════════════════════
# TestPO_GRN_QC_PB_Multi_Item_Single_GP
# ══════════════════════════════════════════════════════════════════════════════

_MI_GP_N_ITEMS  = 5
_MI_GP_ITEM_QTY = 40
_MI_GP_BAGS     = 3


@pytest.mark.integration
class TestPO_GRN_QC_PB_Multi_Item_Single_GP:
    """Sequential E2E: 5-item PO → 1 GP (all items, full qty) → GRN → QC → PB."""

    def test_step1_create_po(self, po_page, integration_state):
        total, row_dicts, supplier_name, location, po_ref_no = \
            po_page.create_record_for_integration(
                item_configs=[(_MI_GP_ITEM_QTY, 0, 0)] * _MI_GP_N_ITEMS
            )

        assert po_ref_no and len(row_dicts) == _MI_GP_N_ITEMS
        integration_state.update({
            "po_ref_no":     po_ref_no,
            "supplier_name": supplier_name,
            "location":      location,
            "item_names":    [rd["item_name"] for rd in row_dicts],
            "rates":         {rd["item_name"]: rd["rate"] for rd in row_dicts},
        })
        items_str = ", ".join(f"{rd['item_name']}×{_MI_GP_ITEM_QTY}" for rd in row_dicts)
        print(f"\n[PO] ref={po_ref_no}  supplier={supplier_name}  items=[{items_str}]")

    def test_step2_create_gp(self, gp_page, integration_state):
        if not integration_state.get("po_ref_no"):
            pytest.skip("PO not created in step 1")

        items = [(name, _MI_GP_BAGS, _MI_GP_ITEM_QTY) for name in integration_state["item_names"]]
        gp_multi = GPPlaywrightPageItemCategory(gp_page.page)
        gp_multi.fill_items_form(
            supplier_name=integration_state["supplier_name"],
            items=items,
            location=integration_state["location"],
            type_of_sale="B2B",
            po_ref_no=integration_state["po_ref_no"],
        )
        gp_ref_no, _ = gp_multi.submit_items_form(items)
        assert gp_ref_no
        integration_state["gp_ref_no"] = gp_ref_no
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
            assert abs(actual_gp_qty - _MI_GP_ITEM_QTY) < 0.5
            grn_page.fill_accepted_qty_nth(i, _MI_GP_ITEM_QTY)

        grn_ref_no = grn_page.submit()
        assert grn_ref_no
        integration_state["grn_ref_no"] = grn_ref_no
        print(f"\n[GRN] ref={grn_ref_no}  rows={n_rows}")

    def test_step4_qc(self, qc_page, integration_state):
        if not integration_state.get("grn_ref_no"):
            pytest.skip("GRN not created in step 3")

        qc_ref_no = qc_page.create_for_integration(
            supplier_name=integration_state["supplier_name"],
            gp_ref_no=integration_state["gp_ref_no"],
            accepted_qty=[_MI_GP_ITEM_QTY] * _MI_GP_N_ITEMS,
        )
        assert qc_ref_no
        integration_state["qc_ref_no"] = qc_ref_no
        print(f"\n[QC] ref={qc_ref_no}  rows={_MI_GP_N_ITEMS}")

    def test_step5_create_pb(self, pb_page, integration_state):
        if not integration_state.get("qc_ref_no"):
            pytest.skip("QC not created in step 4")

        pb_ref_no = pb_page.create_for_integration(
            supplier_name=integration_state["supplier_name"],
            qc_ref_no=integration_state["qc_ref_no"],
        )
        assert pb_ref_no
        integration_state["pb_ref_no"] = pb_ref_no
        print(f"\n[PB] ref={pb_ref_no}  rows={_MI_GP_N_ITEMS}")


# ══════════════════════════════════════════════════════════════════════════════
# TestPO_GRN_QC_PB_Multi_GP
# ══════════════════════════════════════════════════════════════════════════════

_MULTI_GP_N_ITEMS     = 5
_MULTI_GP_QTY_RANGE   = (80, 150)
_MULTI_GP_N_GPS_RANGE = (1,2)


def _split_qty(total, n):
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
    gp_items = [[] for _ in range(n_gps)]
    for name, total_qty in zip(item_names, item_qtys):
        n_assigned = random.randint(1, min(n_gps, total_qty))
        assigned   = random.sample(range(n_gps), n_assigned)
        splits     = _split_qty(total_qty, n_assigned)
        for gp_idx, qty in zip(assigned, splits):
            gp_items[gp_idx].append((name, random.randint(1, 5), int(qty)))
    for i, gp in enumerate(gp_items):
        if not gp:
            for other in gp_items:
                if len(other) > 1:
                    gp_items[i].append(other.pop())
                    break
    return gp_items


@pytest.mark.integration
class TestPO_GRN_QC_PB_Multi_GP:
    """Dynamic sequential E2E: 5-item PO → random 2-5 GPs → each GP→GRN→QC→PB."""

    def test_step1_create_po(self, po_page, integration_state):
        item_configs = [(random.randint(*_MULTI_GP_QTY_RANGE), 0, 0)
                        for _ in range(_MULTI_GP_N_ITEMS)]
        total, row_dicts, supplier_name, location, po_ref_no = \
            po_page.create_record_for_integration(item_configs=item_configs)

        assert po_ref_no and len(row_dicts) == _MULTI_GP_N_ITEMS
        integration_state.update({
            "po_ref_no":     po_ref_no,
            "supplier_name": supplier_name,
            "location":      location,
            "item_names":    [rd["item_name"] for rd in row_dicts],
            "item_qtys":     [cfg[0] for cfg in item_configs],
        })
        items_str = ", ".join(f"{rd['item_name']}×{cfg[0]}" for rd, cfg in zip(row_dicts, item_configs))
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
            gp_multi = GPPlaywrightPageItemCategory(gp_page.page)
            gp_multi.navigate_to_page()
            gp_multi.fill_items_form(supplier, items, location=location,
                                     type_of_sale="B2B", po_ref_no=po_ref_no)
            gp_ref, _ = gp_multi.submit_items_form(items)
            assert gp_ref, f"GP{i+1} ref must be non-empty"
            print(f"\n[GP{i+1}] ref={gp_ref}")

            qty_by_name = {item[0]: item[2] for item in items}
            grn_page.navigate_to_page()
            grn_page.open_add_form()
            grn_page.select_supplier(supplier)
            grn_page.select_gate_pass(gp_ref)
            grn_page.fill_conversion_rate("1")
            for j, name in enumerate(grn_page.read_row_item_names()):
                grn_page.fill_accepted_qty_nth(j, qty_by_name.get(name, 1))
            grn_ref = grn_page.submit()
            assert grn_ref, f"GRN{i+1} ref must be non-empty"
            print(f"\n[GRN{i+1}] ref={grn_ref}")

            accepted_qty_map = {item[0]: item[2] for item in items}
            qc_page.navigate_to_page()
            qc_ref, _ = qc_page.create_for_integration(
                supplier_name=supplier,
                gp_ref_no=gp_ref,
                accepted_qty=accepted_qty_map if len(items) > 1 else list(accepted_qty_map.values())[0],
            )
            assert qc_ref, f"QC{i+1} ref must be non-empty"
            print(f"\n[QC{i+1}] ref={qc_ref}")

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


# ══════════════════════════════════════════════════════════════════════════════
# TestQCWeightToggle
# ══════════════════════════════════════════════════════════════════════════════

_WT_N_ITEMS         = random.randint(3, 5)
_WT_ITEM_QTY        = 50
_WT_GP_BAGS         = 2
_WT_WEIGHT_MODE_ROWS = [i for i in range(_WT_N_ITEMS) if i % 2 == 0]


@pytest.mark.integration
class TestQCWeightToggle:
    """7-9 item PO → GP → GRN → QC with alternating Weight/Rate toggle per row."""

    def test_step1_create_po(self, po_page, integration_state):
        total, row_dicts, supplier_name, location, po_ref_no = \
            po_page.create_record_for_integration(
                item_configs=[(_WT_ITEM_QTY, 0, 0)] * _WT_N_ITEMS
            )

        assert po_ref_no and len(row_dicts) == _WT_N_ITEMS
        integration_state.update({
            "po_ref_no":     po_ref_no,
            "supplier_name": supplier_name,
            "location":      location,
            "item_names":    [rd["item_name"] for rd in row_dicts],
        })
        items_str = ", ".join(f"{rd['item_name']}×{_WT_ITEM_QTY}" for rd in row_dicts)
        print(f"\n[PO] ref={po_ref_no}  supplier={supplier_name}  items=[{items_str}]")

    def test_step2_create_gp(self, gp_page, integration_state):
        if not integration_state.get("po_ref_no"):
            pytest.skip("PO not created in step 1")

        gp = GPPlaywrightPageItemCategory(gp_page.page)
        items = [(name, _WT_GP_BAGS, _WT_ITEM_QTY) for name in integration_state["item_names"]]
        gp.fill_items_form(
            supplier_name=integration_state["supplier_name"],
            items=items,
            location=integration_state["location"],
            type_of_sale="B2B",
            po_ref_no=integration_state["po_ref_no"],
        )
        gp_ref_no, _ = gp.submit_items_form(items)
        assert gp_ref_no
        integration_state["gp_ref_no"] = gp_ref_no
        print(f"\n[GP] ref={gp_ref_no}")

    def test_step3_create_grn(self, grn_page, integration_state):
        if not integration_state.get("gp_ref_no"):
            pytest.skip("GP not created in step 2")

        grn_page.open_add_form()
        grn_page.select_supplier(integration_state["supplier_name"])
        grn_page.select_gate_pass(integration_state["gp_ref_no"])
        grn_page.fill_conversion_rate("1")

        n_rows = grn_page.count_grn_rows()
        assert n_rows == _WT_N_ITEMS, f"Expected {_WT_N_ITEMS} GRN rows, got {n_rows}"
        for i in range(n_rows):
            grn_page.fill_accepted_qty_nth(i, _WT_ITEM_QTY)

        grn_ref_no = grn_page.submit()
        assert grn_ref_no
        integration_state["grn_ref_no"] = grn_ref_no
        print(f"\n[GRN] ref={grn_ref_no}")

    def test_step4_create_qc(self, logged_in_page, integration_state):
        if not integration_state.get("grn_ref_no"):
            pytest.skip("GRN not created in step 3")

        qc = QCPlaywrightPage(logged_in_page)
        qc.navigate_to_page()

        qc_ref_no, row_data = qc.create_for_integration(
            supplier_name=integration_state["supplier_name"],
            gp_ref_no=integration_state["gp_ref_no"],
            accepted_qty=[_WT_ITEM_QTY] * _WT_N_ITEMS,
            weight_mode_rows=_WT_WEIGHT_MODE_ROWS,
        )

        assert qc_ref_no
        integration_state["qc_ref_no"]   = qc_ref_no
        integration_state["qc_row_data"] = row_data
        print(f"\n[QC] ref={qc_ref_no}  n_items={_WT_N_ITEMS}  weight_rows={_WT_WEIGHT_MODE_ROWS}")
        for i, rd in enumerate(row_data):
            mode = "Weight" if rd["use_weight_mode"] else "Rate"
            print(f"  row {i}: mode={mode}  base_rate={rd['base_rate']}  "
                  f"qc_deduction_amount={rd['qc_deduction_amount']}  "
                  f"transaction_amount={rd['transaction_amount']}")

    def test_step5_verify_qc_record(self, logged_in_page, integration_state):
        if not integration_state.get("qc_ref_no"):
            pytest.skip("QC not created in step 4")

        qc       = QCPlaywrightPage(logged_in_page)
        ref_no   = integration_state["qc_ref_no"]
        row_data = integration_state["qc_row_data"]

        print(f"\n[VERIFY] Opening QC record {ref_no}...")
        qc.open_qc_record(ref_no)

        for i, rd in enumerate(row_data):
            calc = qc._read_row_calc_fields(nth=i)
            print(f"  [POST-SUBMIT] row {i}: base_rate={calc['base_rate']}  "
                  f"qc_deduction_amount={calc['qc_deduction_amount']}  "
                  f"transaction_amount={calc['transaction_amount']}")

            assert abs(calc["qc_deduction_amount"] - rd["qc_deduction_amount"]) < 1.0, (
                f"Row {i} QC Deduction Amount changed after save: "
                f"pre={rd['qc_deduction_amount']}, post={calc['qc_deduction_amount']}"
            )
            assert abs(calc["transaction_amount"] - rd["transaction_amount"]) < 1.0, (
                f"Row {i} Transaction Amount changed after save: "
                f"pre={rd['transaction_amount']}, post={calc['transaction_amount']}"
            )

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
                print(f"  [POST-SUBMIT] row {i} Rate: qc_deduction_amount={calc['qc_deduction_amount']} ✓")

    def test_step6_create_pb(self, logged_in_page, integration_state):
        if not integration_state.get("qc_ref_no"):
            pytest.skip("QC not created in step 4")

        pb = PBPlaywrightPage(logged_in_page)
        pb.navigate_to_page()

        pb_ref_no = pb.create_for_integration(
            supplier_name=integration_state["supplier_name"],
            qc_ref_no=integration_state["qc_ref_no"],
        )
        assert pb_ref_no
        integration_state["pb_ref_no"] = pb_ref_no
        print(f"\n[PB] ref={pb_ref_no}")


# ══════════════════════════════════════════════════════════════════════════════
# TestGRNQuantityExceedsPOError
# ══════════════════════════════════════════════════════════════════════════════

_EXCEED_PO_QTY  = 1000   # PO qty = GP qty (no mismatch at GP level)
_EXCEED_GP_QTY  = 1000
_EXCEED_GP_BAGS = 2
_EXCEED_GRN_QTY = 1001   # one over PO balance → triggers backend rejection

_EXCEED_ERROR_TEXT = "GRN quantity should be less than PO quantity. Please Update PO quantity!"


@pytest.mark.integration
class TestGRNQuantityExceedsPOError:
    """PO=1000, GP=1000 (matched), but GRN accepted qty=1001 → toast error.

    The ERP rejects a GRN whose accepted quantity exceeds the linked PO's
    alternate balance, even when GP qty matches PO qty perfectly.
    Expected toast (css: div.swal2-popup.swal2-toast):
        "GRN quantity should be less than PO quantity. Please Update PO quantity!"
    """

    def test_step1_create_po(self, po_page, integration_state):
        total, row_dicts, supplier_name, location, po_ref_no = \
            po_page.create_record_for_integration(item_configs=[(_EXCEED_PO_QTY, 0, 0)])

        assert po_ref_no and len(row_dicts) == 1
        integration_state.update({
            "po_ref_no":     po_ref_no,
            "supplier_name": supplier_name,
            "location":      location,
            "item_names":    [row_dicts[0]["item_name"]],
        })
        print(f"\n[PO] ref={po_ref_no}  qty={_EXCEED_PO_QTY}  item={row_dicts[0]['item_name']}")

    def test_step2_create_gp(self, gp_page, integration_state):
        if not integration_state.get("po_ref_no"):
            pytest.skip("PO not created in step 1")

        gp = GPPlaywrightPageItemCategory(gp_page.page)
        items = [(integration_state["item_names"][0], _EXCEED_GP_BAGS, _EXCEED_GP_QTY)]
        gp.fill_items_form(
            supplier_name=integration_state["supplier_name"],
            items=items,
            location=integration_state["location"],
            type_of_sale="B2B",
            po_ref_no=integration_state["po_ref_no"],
        )
        gp_ref_no, _ = gp.submit_items_form(items)
        assert gp_ref_no
        integration_state["gp_ref_no"] = gp_ref_no
        print(f"\n[GP] ref={gp_ref_no}  qty={_EXCEED_GP_QTY}  (matches PO qty={_EXCEED_PO_QTY})")

    def test_step3_grn_exceeds_po_qty_error(self, grn_page, integration_state):
        """Submit GRN with accepted qty=1001 > PO balance=1000 — assert toast error fires."""
        if not integration_state.get("gp_ref_no"):
            pytest.skip("GP not created in step 2")

        page = grn_page.page
        grn_page.open_add_form()
        grn_page.select_supplier(integration_state["supplier_name"])
        grn_page.select_gate_pass(integration_state["gp_ref_no"])
        grn_page.fill_conversion_rate("1")
        page.wait_for_timeout(800)

        # Fill received qty ONE over the PO balance to trigger the error
        grn_page.fill_received_qty_nth(0, _EXCEED_GRN_QTY)
        page.wait_for_timeout(300)

        page.locator(grn_page.SUBMIT_BTN).click()

        toast = page.locator("div.swal2-popup.swal2-toast")
        toast.wait_for(state="visible", timeout=10000)
        toast_text = toast.inner_text().strip()

        print(f"\n[GRN] Toast received: {toast_text!r}")
        assert _EXCEED_ERROR_TEXT in toast_text, (
            f"Expected toast to contain:\n  {_EXCEED_ERROR_TEXT!r}\n"
            f"Got:\n  {toast_text!r}"
        )
        print(
            f"  [GRN] Error toast ✓ — ERP correctly rejected "
            f"accepted qty={_EXCEED_GRN_QTY} > PO balance={_EXCEED_PO_QTY}"
        )

        # Dismiss toast and cancel form
        try:
            page.wait_for_selector("div.swal2-popup.swal2-toast", state="hidden", timeout=6000)
        except Exception:
            pass
        page.locator(grn_page.CANCEL_BTN).click(force=True)
        page.wait_for_timeout(500)


# ══════════════════════════════════════════════════════════════════════════════
# TestGRNPOBalanceQuantity
# ══════════════════════════════════════════════════════════════════════════════

_BAL_PO_QTY  = 100   # total PO quantity
_BAL_GP1_QTY = 60    # first GP takes 60
_BAL_GP2_QTY = 40    # second GP takes remaining 40
_BAL_GP_BAGS = 2


@pytest.mark.integration
class TestGRNPOBalanceQuantity:
    """1-item PO → 2 GPs → assert PO Quantity and PO Balance Quantity in each GRN.

    GRN field logic (from purchase_chain.py):
        PO Quantity       = full PO line qty (constant across all GRNs)
        PO Balance Qty    = PO Quantity − total already received in prior GRNs

    GRN1: PO Qty = _BAL_PO_QTY,  PO Balance Qty = _BAL_PO_QTY        (nothing received yet)
    GRN2: PO Qty = _BAL_PO_QTY,  PO Balance Qty = _BAL_PO_QTY − _BAL_GP1_QTY
    """

    def test_step1_create_po(self, po_page, integration_state):
        total, row_dicts, supplier_name, location, po_ref_no = \
            po_page.create_record_for_integration(item_configs=[(_BAL_PO_QTY, 0, 0)])

        assert po_ref_no and len(row_dicts) == 1
        integration_state.update({
            "po_ref_no":     po_ref_no,
            "supplier_name": supplier_name,
            "location":      location,
            "item_names":    [row_dicts[0]["item_name"]],
        })
        print(f"\n[PO] ref={po_ref_no}  qty={_BAL_PO_QTY}  item={row_dicts[0]['item_name']}")

    def test_step2_create_gp1(self, gp_page, integration_state):
        if not integration_state.get("po_ref_no"):
            pytest.skip("PO not created in step 1")

        gp = GPPlaywrightPageItemCategory(gp_page.page)
        items = [(integration_state["item_names"][0], _BAL_GP_BAGS, _BAL_GP1_QTY)]
        gp.fill_items_form(
            supplier_name=integration_state["supplier_name"],
            items=items,
            location=integration_state["location"],
            type_of_sale="B2B",
            po_ref_no=integration_state["po_ref_no"],
        )
        gp_ref_no, _ = gp.submit_items_form(items)
        assert gp_ref_no
        integration_state["gp1_ref_no"] = gp_ref_no
        print(f"\n[GP1] ref={gp_ref_no}  qty={_BAL_GP1_QTY}")

    def test_step3_grn1_po_balance_assert(self, grn_page, integration_state):
        """GRN1: PO Qty = full PO qty, PO Balance Qty = full PO qty (nothing received yet)."""
        if not integration_state.get("gp1_ref_no"):
            pytest.skip("GP1 not created in step 2")

        grn_page.open_add_form()
        grn_page.select_supplier(integration_state["supplier_name"])
        grn_page.select_gate_pass(integration_state["gp1_ref_no"])
        grn_page.fill_conversion_rate("1")
        grn_page.page.wait_for_timeout(800)

        po_qty     = grn_page.read_po_qty_nth(0)
        bal_qty    = grn_page.read_po_balance_qty_nth(0)

        print(f"\n[GRN1] PO Quantity={po_qty}  PO Balance Quantity={bal_qty}")
        assert abs(po_qty - _BAL_PO_QTY) < 0.5, (
            f"GRN1 PO Quantity: expected {_BAL_PO_QTY}, got {po_qty}"
        )
        assert abs(bal_qty - _BAL_PO_QTY) < 0.5, (
            f"GRN1 PO Balance Quantity: expected {_BAL_PO_QTY} (nothing received yet), got {bal_qty}"
        )
        print(f"  [GRN1] PO Qty ✓ ({po_qty})  PO Balance Qty ✓ ({bal_qty})")

        grn_page.fill_accepted_qty_nth(0, _BAL_GP1_QTY)
        grn_ref_no = grn_page.submit()
        assert grn_ref_no
        integration_state["grn1_ref_no"] = grn_ref_no
        print(f"\n[GRN1] ref={grn_ref_no}")

    def test_step4_create_gp2(self, gp_page, integration_state):
        if not integration_state.get("grn1_ref_no"):
            pytest.skip("GRN1 not created in step 3")

        gp = GPPlaywrightPageItemCategory(gp_page.page)
        items = [(integration_state["item_names"][0], _BAL_GP_BAGS, _BAL_GP2_QTY)]
        gp.fill_items_form(
            supplier_name=integration_state["supplier_name"],
            items=items,
            location=integration_state["location"],
            type_of_sale="B2B",
            po_ref_no=integration_state["po_ref_no"],
        )
        gp_ref_no, _ = gp.submit_items_form(items)
        assert gp_ref_no
        integration_state["gp2_ref_no"] = gp_ref_no
        print(f"\n[GP2] ref={gp_ref_no}  qty={_BAL_GP2_QTY}")

    def test_step5_grn2_po_balance_assert(self, grn_page, integration_state):
        """GRN2: PO Qty = full PO qty, PO Balance Qty = PO qty − GP1 qty already received."""
        if not integration_state.get("gp2_ref_no"):
            pytest.skip("GP2 not created in step 4")

        grn_page.open_add_form()
        grn_page.select_supplier(integration_state["supplier_name"])
        grn_page.select_gate_pass(integration_state["gp2_ref_no"])
        grn_page.fill_conversion_rate("1")
        grn_page.page.wait_for_timeout(800)

        po_qty  = grn_page.read_po_qty_nth(0)
        bal_qty = grn_page.read_po_balance_qty_nth(0)
        expected_balance = _BAL_PO_QTY - _BAL_GP1_QTY  # 100 - 60 = 40

        print(f"\n[GRN2] PO Quantity={po_qty}  PO Balance Quantity={bal_qty}  expected_balance={expected_balance}")
        assert abs(po_qty - _BAL_PO_QTY) < 0.5, (
            f"GRN2 PO Quantity: expected {_BAL_PO_QTY}, got {po_qty}"
        )
        assert abs(bal_qty - expected_balance) < 0.5, (
            f"GRN2 PO Balance Quantity: expected {expected_balance} "
            f"({_BAL_PO_QTY} − {_BAL_GP1_QTY} already received), got {bal_qty}"
        )
        print(f"  [GRN2] PO Qty ✓ ({po_qty})  PO Balance Qty ✓ ({bal_qty} = {_BAL_PO_QTY}−{_BAL_GP1_QTY})")

        grn_page.fill_accepted_qty_nth(0, _BAL_GP2_QTY)
        grn_ref_no = grn_page.submit()
        assert grn_ref_no
        integration_state["grn2_ref_no"] = grn_ref_no
        print(f"\n[GRN2] ref={grn_ref_no}")


# ══════════════════════════════════════════════════════════════════════════════
# TestCalculationAssertions
# ══════════════════════════════════════════════════════════════════════════════

_CALC_ITEM_QTY        = 50
_CALC_GP_BAGS         = 2
_CALC_BAGS            = 3      # No of Bags in QC bags popup
_CALC_PER_BAG_WT      = 5.0    # Per Bag Weight in QC bags popup
_CALC_FIXED_LABOUR    = 10.0   # Labour Charges override in PB
_CALC_FIXED_TRANSPORT = 50.0   # Transport Charges override in PB


@pytest.mark.integration
class TestCalculationAssertions:
    """1-item PO → GP → GRN → QC (Total Weight) → PB (Total Amount) with formula assertions."""

    def test_step1_create_po(self, po_page, integration_state):
        total, row_dicts, supplier_name, location, po_ref_no = \
            po_page.create_record_for_integration(item_configs=[(_CALC_ITEM_QTY, 0, 0)])

        assert po_ref_no and len(row_dicts) == 1
        integration_state.update({
            "po_ref_no":     po_ref_no,
            "supplier_name": supplier_name,
            "location":      location,
            "item_names":    [row_dicts[0]["item_name"]],
        })
        print(f"\n[PO] ref={po_ref_no}  item={row_dicts[0]['item_name']}×{_CALC_ITEM_QTY}")

    def test_step2_create_gp(self, gp_page, integration_state):
        if not integration_state.get("po_ref_no"):
            pytest.skip("PO not created in step 1")

        gp = GPPlaywrightPageItemCategory(gp_page.page)
        items = [(integration_state["item_names"][0], _CALC_GP_BAGS, _CALC_ITEM_QTY)]
        gp.fill_items_form(
            supplier_name=integration_state["supplier_name"],
            items=items,
            location=integration_state["location"],
            type_of_sale="B2B",
            po_ref_no=integration_state["po_ref_no"],
        )
        gp_ref_no, _ = gp.submit_items_form(items)
        assert gp_ref_no
        integration_state["gp_ref_no"] = gp_ref_no
        print(f"\n[GP] ref={gp_ref_no}")

    def test_step3_create_grn(self, grn_page, integration_state):
        if not integration_state.get("gp_ref_no"):
            pytest.skip("GP not created in step 2")

        grn_page.open_add_form()
        grn_page.select_supplier(integration_state["supplier_name"])
        grn_page.select_gate_pass(integration_state["gp_ref_no"])
        grn_page.fill_conversion_rate("1")
        grn_page.fill_accepted_qty_nth(0, _CALC_ITEM_QTY)
        grn_ref_no = grn_page.submit()
        assert grn_ref_no
        integration_state["grn_ref_no"] = grn_ref_no
        print(f"\n[GRN] ref={grn_ref_no}")

    def test_step4_qc_total_weight_assert(self, logged_in_page, integration_state):
        if not integration_state.get("grn_ref_no"):
            pytest.skip("GRN not created in step 3")

        qc = QCPlaywrightPage(logged_in_page)
        qc.navigate_to_page()
        qc.open_add_form()
        qc.select_supplier(integration_state["supplier_name"])
        qc.select_item_category("Raw Materia")
        qc.select_gate_pass(integration_state["gp_ref_no"])
        qc.fill_conversion_rate(1)

        qc._js_fill_by_placeholder("Net Qty", _CALC_ITEM_QTY, nth=0)
        qc._js_fill_by_placeholder("Discount Rate", 1, nth=0)
        logged_in_page.wait_for_timeout(300)
        qc.fill_quality_parameters(actual_value=1, row=0)

        btn_sel     = "button[data-sd-details-opener='qc_details[0].qc_bags_details']"
        section_sel = "[data-sd-section-path='qc_details[0].qc_bags_details']"
        btn = logged_in_page.locator(btn_sel).first
        btn.scroll_into_view_if_needed()
        logged_in_page.wait_for_timeout(300)
        btn.click(force=True)
        logged_in_page.wait_for_selector(section_sel, timeout=15000)
        logged_in_page.wait_for_timeout(500)

        logged_in_page.locator(qc.BAGS_TYPE_SELECT).first.click(force=True)
        logged_in_page.wait_for_selector(".mat-mdc-select-panel", timeout=5000)
        logged_in_page.locator(
            ".mat-mdc-select-panel mat-option:not(.dd-clear-option)"
        ).first.click(force=True)
        try:
            logged_in_page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
        except Exception:
            pass
        logged_in_page.wait_for_timeout(300)

        qc._js_fill_by_placeholder("No of  Bag", _CALC_BAGS, nth=0)
        logged_in_page.wait_for_timeout(400)
        qc._js_fill_by_placeholder("Per Bag Weight", _CALC_PER_BAG_WT, nth=0)
        logged_in_page.wait_for_timeout(400)

        actual_tw   = _js_read_num_by_label(logged_in_page, "Total Weight", nth=0)
        expected_tw = _CALC_BAGS * _CALC_PER_BAG_WT
        assert actual_tw is not None, "Total Weight field not found"
        assert abs(actual_tw - expected_tw) < 0.01, (
            f"Total Weight mismatch: expected {expected_tw} ({_CALC_BAGS} × {_CALC_PER_BAG_WT}), got {actual_tw}"
        )
        print(
            f"\n[QC] Total Weight: {_CALC_BAGS} bags × {_CALC_PER_BAG_WT} kg/bag "
            f"= {expected_tw} kg ✓ (actual={actual_tw})"
        )

        logged_in_page.locator(qc.POPUP_DONE_BTN).click(force=True)
        logged_in_page.wait_for_timeout(500)

        qc_ref_no = qc.submit()
        assert qc_ref_no
        integration_state["qc_ref_no"] = qc_ref_no
        print(f"\n[QC] ref={qc_ref_no}")

    def test_step5_pb_total_amount_assert(self, logged_in_page, integration_state):
        if not integration_state.get("qc_ref_no"):
            pytest.skip("QC not created in step 4")

        pb = PBPlaywrightPage(logged_in_page)
        pb.navigate_to_page()
        pb.open_add_form()
        pb.select_supplier(integration_state["supplier_name"])
        pb.select_qc(integration_state["qc_ref_no"])
        pb.fill_conversion_rate(1)
        logged_in_page.wait_for_timeout(1000)

        pb_amount = _js_read_num_by_label(logged_in_page, "QC Transaction Amount", nth=0)
        assert pb_amount is not None and pb_amount > 0, (
            f"QC Transaction Amount not auto-populated after QC selection, got {pb_amount}"
        )
        print(f"\n[PB] Auto-populated QC Transaction Amount = {pb_amount}")

        pb.fill_row(0)
        logged_in_page.wait_for_timeout(300)

        def _override_field(label, value):
            logged_in_page.evaluate(
                """
                ([label, value]) => {
                    const fields = [...document.querySelectorAll('mat-form-field')].filter(f =>
                        f.querySelector('mat-label')?.textContent.trim() === label
                    );
                    const el = fields[0]?.querySelector('input');
                    if (!el) return false;
                    const setter = Object.getOwnPropertyDescriptor(
                        window.HTMLInputElement.prototype, 'value'
                    ).set;
                    setter.call(el, String(value));
                    el.dispatchEvent(new Event('input', {bubbles: true}));
                    el.dispatchEvent(new Event('change', {bubbles: true}));
                    return true;
                }
                """,
                [label, value],
            )

        def _override_placeholder(placeholder, value):
            logged_in_page.evaluate(
                """
                ([ph, value]) => {
                    const el = document.querySelector(`input[placeholder="${ph}"]`);
                    if (!el) return false;
                    const setter = Object.getOwnPropertyDescriptor(
                        window.HTMLInputElement.prototype, 'value'
                    ).set;
                    setter.call(el, String(value));
                    el.dispatchEvent(new Event('input', {bubbles: true}));
                    el.dispatchEvent(new Event('change', {bubbles: true}));
                    return true;
                }
                """,
                [placeholder, value],
            )

        _override_field("Labour Charges", _CALC_FIXED_LABOUR)
        logged_in_page.wait_for_timeout(300)
        _override_placeholder("Transport charges", _CALC_FIXED_TRANSPORT)
        logged_in_page.wait_for_timeout(600)

        gst          = _js_read_num_by_label(logged_in_page, "Tax amount", nth=0) or 0.0
        actual_total = _js_read_num_by_label(logged_in_page, "Total Amount", nth=0)

        # Discount already baked into QC Transaction Amount; do NOT deduct again
        # Transport Charges subtracted like Labour Charges
        expected_total = pb_amount + gst - _CALC_FIXED_LABOUR - _CALC_FIXED_TRANSPORT

        print(
            f"\n[PB] Formula check:\n"
            f"  QC Transaction Amount={pb_amount}  Tax amount={gst}  "
            f"Labour={_CALC_FIXED_LABOUR}  Transport={_CALC_FIXED_TRANSPORT}\n"
            f"  Expected Total = {expected_total:.2f}  Actual Total = {actual_total}"
        )

        assert actual_total is not None, "Total Amount field not found in PB form"
        assert abs(actual_total - expected_total) < 1.0, (
            f"PB Total Amount mismatch: expected {expected_total:.2f}, got {actual_total}"
        )
        print(f"[PB] Total Amount assertion ✓")

        pb_ref_no = pb.submit()
        assert pb_ref_no
        integration_state["pb_ref_no"] = pb_ref_no
        print(f"\n[PB] ref={pb_ref_no}")

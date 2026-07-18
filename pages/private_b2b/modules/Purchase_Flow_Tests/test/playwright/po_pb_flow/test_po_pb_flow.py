"""
PO -> PB direct flow tests (Rolex Traders tenant).

Flow: create PO -> create PB directly against it (no GP / GRN / QC).

Classes:
  TestPO_PB_DirectFlow   -- single-item PO with disc/int -> PB qty/rate/txn assertions
  TestPO_PB_MultiRow     -- 2-item PO with per-row disc/int -> PB assertions per row
  TestPO_PB_CustomRate   -- manually override PO rate -> PB must carry the new rate
  TestPO_PB_NoGST        -- PO with GST off -> PB txn = qty x rate (no tax)
  TestPOValidations      -- PO form validation rules (Rolex Traders tenant)
  TestPBValidations      -- PB form validation rules (Rolex Traders tenant)
"""

import pytest


# ── Shared assertion helper ───────────────────────────────────────────────────

def _assert_pb_rows(po_rows, pb_rows, po_ref_no):
    """Row-level assertion + pretty-print used by multi-row PB test steps."""
    assert len(pb_rows) == len(po_rows), (
        f"PB row count {len(pb_rows)} != PO row count {len(po_rows)}"
    )
    print(f"\n  PO: {po_ref_no}")
    print(f"  {'Row':<4} {'Item':<20} {'PO qty':>7} {'PB qty':>7} {'Rate':>9} "
          f"{'Disc%':>6} {'Int%':>5} {'PO txn':>11} {'PB txn':>11}")
    print(f"  {'-'*85}")

    for i, (po_r, pb_r) in enumerate(zip(po_rows, pb_rows)):
        po_qty  = int(po_r["qty"])
        po_rate = po_r["rate"]
        disc    = po_r.get("disc_pct", 0) or 0
        intr    = po_r.get("int_pct", 0) or 0
        po_txn  = po_r["txn_amount"]
        pb_qty  = pb_r["net_qty"]
        pb_rate = pb_r["rate"]
        pb_txn  = pb_r["txn_amount"]

        assert pb_qty == po_qty, f"Row {i}: PB qty {pb_qty} != PO qty {po_qty}"
        assert abs(pb_rate - po_rate) < 0.01, (
            f"Row {i}: PB rate {pb_rate} != PO rate {po_rate}"
        )
        assert abs(pb_txn - po_txn) < 1.0, (
            f"Row {i}: PB txn {pb_txn} != PO txn {po_txn} "
            f"(qty={po_qty}, rate={po_rate}, disc={disc}%, int={intr}%)"
        )
        print(f"  {i:<4} {po_r['item_name']:<20} {po_qty:>7} {pb_qty:>7} {po_rate:>9.2f} "
              f"{disc:>6} {intr:>5} {po_txn:>11.2f} {pb_txn:>11.2f}")

    print(f"  {'-'*85}")


# ── Single-item flow (with discount & interest) ───────────────────────────────

@pytest.mark.po_pb
class TestPO_PB_DirectFlow:

    def test_single_item_flow(self, pb_page, po_page):
        """Single-item PO (disc=5%, int=2%) -> PB qty/rate/txn must match."""
        total, row_dicts, supplier_name, _, ref_no = \
            po_page.create_record_for_integration(item_configs=[(10, 5, 2)])

        assert ref_no,        "PO ref_no must be non-empty"
        assert supplier_name, "Supplier must be captured"
        assert total > 0,     "PO total must be > 0"

        r = row_dicts[0]
        print("\n" + "=" * 60)
        print(f"  PO created:    {ref_no}  |  Supplier: {supplier_name}")
        print(f"  Item: {r['item_name']}  Rate: {r['rate']:.2f}  Qty: {r['qty']}")
        print(f"  Disc%: {r['disc_pct']}  Int%: {r['int_pct']}  Txn: {r['txn_amount']:.2f}")
        print(f"  PO Total: {total:.2f}")

        row_configs  = [(1, int(r["qty"])) for r in row_dicts]
        pb_page.navigate_to_page()
        total_amount, pb_rows = pb_page.create_record_from_po(
            supplier_name, row_configs=row_configs
        )

        assert total_amount > 0, "PB total must be > 0"
        _assert_pb_rows(row_dicts, pb_rows, ref_no)

        pb_txn_sum = sum(r["txn_amount"] for r in pb_rows if r["txn_amount"])
        print(f"  TOTAL  pb_form={total_amount:.2f}  pb_rows_sum={pb_txn_sum:.2f}")
        print("=" * 60)


# ── Multi-item flow (with per-row discount & interest) ────────────────────────

@pytest.mark.po_pb
class TestPO_PB_MultiRow:

    def test_multi_row_flow(self, pb_page, po_page):
        """2-item PO (row0 disc=5%/int=2%, row1 disc=3%/int=1%) -> PB per-row match."""
        total, row_dicts, supplier_name, _, ref_no = \
            po_page.create_record_for_integration(
                item_configs=[(10, 5, 2), (5, 3, 1)]
            )

        assert ref_no,              "PO ref_no must be non-empty"
        assert len(row_dicts) == 2, f"Expected 2 PO rows, got {len(row_dicts)}"
        assert total > 0,           "PO total must be > 0"

        print("\n" + "=" * 60)
        print(f"  PO created: {ref_no}  |  Supplier: {supplier_name}")
        for i, r in enumerate(row_dicts):
            print(f"  Row {i}: {r['item_name']:<20}  qty={r['qty']}  rate={r['rate']:.2f}"
                  f"  disc={r['disc_pct']}%  int={r['int_pct']}%  txn={r['txn_amount']:.2f}")
        print(f"  PO Total: {total:.2f}")

        row_configs  = [(1, int(r["qty"])) for r in row_dicts]
        pb_page.navigate_to_page()
        total_amount, pb_rows = pb_page.create_record_from_po(
            supplier_name, row_configs=row_configs
        )

        assert total_amount > 0, "PB total must be > 0"
        _assert_pb_rows(row_dicts, pb_rows, ref_no)

        pb_txn_sum = sum(r["txn_amount"] for r in pb_rows if r["txn_amount"])
        print(f"  TOTAL  pb_form={total_amount:.2f}  pb_rows_sum={pb_txn_sum:.2f}")
        print("=" * 60)


# ── Custom rate override flow ─────────────────────────────────────────────────

@pytest.mark.po_pb
class TestPO_PB_CustomRate:

    def test_custom_rate_flow(self, pb_page, po_page):
        """PO rate overridden 10% below auto-fetch -> PB must carry the custom rate."""
        po_page.open_add_form()
        supplier_name, _ = po_page.fill_header_returning_supplier()

        item_name = po_page._select_random_mat_option_nth(po_page.ITEM_NAME, 0)
        po_page.page.wait_for_timeout(2000)

        auto_rate = 0.0
        for _ in range(5):
            raw = po_page.page.evaluate("""
                ([xpath, idx]) => {
                    const r = document.evaluate(xpath, document, null,
                        XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                    const el = r.snapshotItem(idx);
                    return el ? el.value : '';
                }
            """, [po_page.RATE.replace("xpath=", ""), 0])
            if raw and float(raw or 0) > 0:
                auto_rate = float(raw)
                break
            po_page.page.wait_for_timeout(800)

        assert auto_rate > 0, "Rate did not auto-fetch after item selection"

        custom_rate = round(auto_rate * 0.90, 2)
        po_page._fill_number_nth(po_page.RATE, 0, custom_rate)
        po_page.page.wait_for_timeout(600)

        qty = 10
        po_page._fill_number_nth(po_page.QUANTITY, 0, qty)
        po_page._fill_number_nth(po_page.DISCOUNT, 0, 0)
        po_page._fill_number_nth(po_page.INTEREST, 0, 0)
        po_page.page.wait_for_timeout(800)

        txn_raw = po_page.page.evaluate("""
            ([xpath, idx]) => {
                const r = document.evaluate(xpath, document, null,
                    XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                const el = r.snapshotItem(idx);
                return el ? el.value : '';
            }
        """, [po_page.TRANSACTION_AMOUNT.replace("xpath=", ""), 0])
        txn_amount = float(txn_raw) if txn_raw and txn_raw.strip() else custom_rate * qty

        assert abs(txn_amount - custom_rate * qty) < 1.0, (
            f"Txn {txn_amount:.2f} != custom_rate {custom_rate:.2f} x qty {qty}"
        )

        po_page.page.locator(po_page.SUBMIT_BTN).click()
        po_page.handle_success_alert()
        po_page.navigate_to_page()
        ref_no = po_page.get_first_ref_no()

        print("\n" + "=" * 60)
        print(f"  PO created: {ref_no}  |  Item: {item_name}")
        print(f"  Auto rate: {auto_rate:.2f}  Custom rate: {custom_rate:.2f}  (-10%)")
        print(f"  Qty: {qty}  Txn: {txn_amount:.2f}")

        po_rows = [{
            "item_name":  item_name,
            "qty":        qty,
            "rate":       custom_rate,
            "disc_pct":   0,
            "int_pct":    0,
            "txn_amount": txn_amount,
        }]

        pb_page.navigate_to_page()
        total_amount, pb_rows = pb_page.create_record_from_po(
            supplier_name, row_configs=[(1, qty)]
        )

        assert total_amount > 0, "PB total must be > 0"
        assert pb_rows,          "PB must have at least one row"

        pb_rate = pb_rows[0]["rate"]
        assert abs(pb_rate - custom_rate) < 0.01, (
            f"PB rate {pb_rate:.2f} should match custom PO rate {custom_rate:.2f}, "
            f"not auto-fetched {auto_rate:.2f}"
        )
        print(f"  PB rate: {pb_rate:.2f}  -> MATCH: {abs(pb_rate - custom_rate) < 0.01}")
        print("=" * 60)


# ── No-GST flow ───────────────────────────────────────────────────────────────

@pytest.mark.po_pb
class TestPO_PB_NoGST:

    def test_no_gst_flow(self, pb_page, po_page):
        """PO with GST off -> txn = qty x rate; PB must match with no tax added."""
        total, row_dicts, supplier_name, _, ref_no = \
            po_page.create_record_for_integration(
                item_configs=[(10, 0, 0)], enable_gst=False
            )

        assert ref_no, "PO ref_no must be non-empty"
        r = row_dicts[0]
        assert not r.get("gst_enabled", False), "GST must be off"
        assert abs(r["txn_amount"] - r["rate"] * r["qty"]) < 0.50, (
            f"Without GST, txn_amount {r['txn_amount']:.2f} != "
            f"rate {r['rate']:.2f} x qty {r['qty']}"
        )

        print("\n" + "=" * 60)
        print(f"  PO created: {ref_no}  (GST OFF)  |  Item: {r['item_name']}")
        print(f"  Rate: {r['rate']:.2f}  Qty: {r['qty']}  Txn: {r['txn_amount']:.2f}")
        print(f"  Tax amount: {r.get('tax_amount', 0):.2f}  (must be 0)")

        pb_page.navigate_to_page()
        total_amount, pb_rows = pb_page.create_record_from_po(
            supplier_name, row_configs=[(1, int(r["qty"]))]
        )

        assert total_amount > 0, "PB total must be > 0"
        pb_r = pb_rows[0]

        assert abs(pb_r["rate"] - r["rate"]) < 0.01, (
            f"PB rate {pb_r['rate']:.2f} != PO rate {r['rate']:.2f}"
        )
        assert abs(pb_r["txn_amount"] - r["txn_amount"]) < 1.0, (
            f"PB txn {pb_r['txn_amount']:.2f} != PO txn {r['txn_amount']:.2f} — "
            f"tax may have been incorrectly applied"
        )
        print(f"  PO txn: {r['txn_amount']:.2f}  PB txn: {pb_r['txn_amount']:.2f}  -> MATCH")
        print("=" * 60)


# ── PO form validations (Rolex Traders tenant) ────────────────────────────────

@pytest.mark.po_pb
class TestPOValidations:

    def _open_with_one_item(self, po_page):
        po_page.open_add_form()
        po_page.fill_header()
        po_page._select_random_mat_option_nth(po_page.ITEM_NAME, 0)
        po_page.page.wait_for_timeout(1500)

    def test_empty_submit_and_cancel(self, po_page):
        """Empty submit keeps form open; cancel returns to listing."""
        po_page.open_add_form()
        po_page.page.locator(po_page.SUBMIT_BTN).click(force=True)
        po_page.page.wait_for_timeout(800)
        assert po_page.page.locator(po_page.SUPPLIER_NAME).count() > 0, \
            "Empty submit must keep form open"
        po_page.close_popup()

        po_page.open_add_form()
        po_page.close_popup()
        assert po_page.page.locator("table.mat-mdc-table").count() > 0, \
            "Listing table must be visible after cancel"

    def test_field_validations(self, po_page):
        """qty=0, negative qty, discount>100, negative interest each show mat-error."""
        # qty = 0
        self._open_with_one_item(po_page)
        po_page._fill_number_nth(po_page.QUANTITY, 0, 10)
        po_page._fill_number_nth(po_page.QUANTITY, 0, 0)
        po_page.page.locator(po_page.SUBMIT_BTN).click(force=True)
        po_page.page.wait_for_timeout(1000)
        assert po_page.page.locator("mat-error").count() > 0, "mat-error must appear for qty=0"
        assert po_page.page.locator(po_page.SUPPLIER_NAME).count() > 0, \
            "Form must stay open on qty=0"
        po_page.close_popup()

        # qty negative
        self._open_with_one_item(po_page)
        po_page._fill_number_nth(po_page.QUANTITY, 0, -1)
        po_page.page.wait_for_timeout(600)
        assert po_page.page.locator("mat-error").count() > 0, \
            "mat-error must appear for negative qty"
        po_page.close_popup()

        # discount > 100
        self._open_with_one_item(po_page)
        po_page._fill_number_nth(po_page.QUANTITY, 0, 10)
        po_page._fill_number_nth(po_page.DISCOUNT, 0, 110)
        po_page.page.wait_for_timeout(600)
        assert po_page.page.locator("mat-error").count() > 0, \
            "mat-error must appear for discount > 100"
        po_page.close_popup()

        # interest negative
        self._open_with_one_item(po_page)
        po_page._fill_number_nth(po_page.QUANTITY, 0, 10)
        po_page._fill_number_nth(po_page.INTEREST, 0, -5)
        po_page.page.locator(po_page.SUBMIT_BTN).click(force=True)
        po_page.page.wait_for_timeout(1000)
        assert po_page.page.locator("mat-error").filter(
            has_text="Interest cannot be less than 0"
        ).count() > 0, "Expected 'Interest cannot be less than 0' mat-error"
        po_page.close_popup()

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
        po_page.close_popup()


# ── PB form validations (Rolex Traders tenant) ────────────────────────────────

@pytest.fixture(scope="class")
def po_for_pb_validation(logged_in_page):
    """Create one PO (single item, qty=20) shared across all TestPBValidations tests."""
    from pages.private_b2b.modules.purchase_order.po_playwright_page import POPlaywrightPage
    po = POPlaywrightPage(logged_in_page)
    po.navigate_to_page()
    _, row_dicts, supplier_name, _, ref_no = po.create_record_for_integration(
        item_configs=[(20, 0, 0)], enable_gst=False
    )
    print(f"\n[PB-VALIDATION FIXTURE] PO {ref_no} created | supplier={supplier_name} | qty=20")
    yield {
        "supplier_name": supplier_name,
        "ref_no":        ref_no,
        "po_qty":        int(row_dicts[0]["qty"]),
        "po_rate":       row_dicts[0]["rate"],
    }


@pytest.mark.po_pb
class TestPBValidations:
    """Validation tests for the PB form on Rolex Traders tenant."""

    # ── helpers ──────────────────────────────────────────────────────────────

    def _open_pb_with_po(self, pb_page, supplier_name):
        pb_page.open_add_form()
        pb_page.select_supplier_and_po(supplier_name)

    def _fill_native(self, pb_page, selector, value):
        """Native click+fill+Tab so Angular validators fire (blur/touched/dirty)."""
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

    def _cancel(self, pb_page):
        try:
            if pb_page.page.locator(pb_page.DONE_BTN).is_visible():
                pb_page.page.keyboard.press("Escape")
                pb_page.page.wait_for_timeout(400)
        except Exception:
            pass
        pb_page.navigate_to_page()
        pb_page.page.wait_for_selector("table.mat-mdc-table, div.empty-state", timeout=10000)

    def _visible_errors(self, pb_page):
        return pb_page.page.evaluate("""
            () => Array.from(document.querySelectorAll('mat-error'))
                       .filter(el => el.offsetParent !== null)
                       .map(el => el.innerText.trim())
        """)

    # ── no-PO tests ──────────────────────────────────────────────────────────

    def test_empty_submit_and_cancel(self, pb_page):
        """Empty submit shows mat-errors and keeps form; cancel returns to listing."""
        pb_page.open_add_form()
        pb_page.page.locator(pb_page.SUBMIT_BTN).click(force=True)
        pb_page.page.wait_for_timeout(1000)
        assert pb_page.page.locator("mat-error").count() > 0, \
            "Expected mat-errors on empty PB submit"
        assert pb_page.page.locator(pb_page.SUPPLIER_NAME).count() > 0, \
            "Form must stay open after empty submit"
        self._cancel(pb_page)

        pb_page.open_add_form()
        self._cancel(pb_page)
        assert pb_page.page.locator("table.mat-mdc-table, div.empty-state").count() > 0, \
            "Listing must be visible after cancel"

    def test_no_po_selected_submit_blocked(self, pb_page, po_for_pb_validation):
        """Supplier selected but no PO -> submit must show mat-errors."""
        pb_page.open_add_form()
        pb_page._select_mat_by_text(pb_page.SUPPLIER_NAME, po_for_pb_validation["supplier_name"])
        pb_page.page.wait_for_timeout(1000)
        pb_page.page.locator(pb_page.SUBMIT_BTN).click(force=True)
        pb_page.page.wait_for_timeout(1000)
        assert pb_page.page.locator("mat-error").count() > 0, \
            "Expected mat-errors when no PO is selected"
        self._cancel(pb_page)

    # ── header field limit tests (all: open PB, fill one field, check error) ─

    def test_header_field_limits_blocked(self, pb_page, po_for_pb_validation):
        """Discount>100, Round Off Credit>1, Round Off Debit>1 each show mat-error."""
        supplier = po_for_pb_validation["supplier_name"]

        # discount > 100
        self._open_pb_with_po(pb_page, supplier)
        self._fill_native(pb_page, pb_page.DISC_PERCENTAGE, 101)
        pb_page.page.locator(pb_page.SUBMIT_BTN).click(force=True)
        pb_page.page.wait_for_timeout(1000)
        assert len(self._visible_errors(pb_page)) > 0, \
            "Expected mat-error for discount > 100"
        self._cancel(pb_page)

        # round off credit > 1
        self._open_pb_with_po(pb_page, supplier)
        self._fill_native(pb_page, pb_page.ROUND_OFF_CREDIT, 2)
        pb_page.page.locator(pb_page.SUBMIT_BTN).click(force=True)
        pb_page.page.wait_for_timeout(1000)
        assert len(self._visible_errors(pb_page)) > 0, \
            "Expected mat-error when Round Off Credit > 1"
        self._cancel(pb_page)

        # round off debit > 1
        self._open_pb_with_po(pb_page, supplier)
        pb_page._fill_number_nth(pb_page.ROUND_OFF_DEBIT, 0, 2)
        pb_page.page.wait_for_timeout(600)
        assert pb_page.page.locator("mat-error").count() > 0, \
            "Expected mat-error when Round Off Debit > 1"
        self._cancel(pb_page)

    # ── qty popup tests (all open the qty popup) ──────────────────────────────

    def test_qty_popup_validations_blocked(self, pb_page, po_for_pb_validation):
        """EBW>qty, labour>gross, qty=0 in popup each show errors."""
        supplier = po_for_pb_validation["supplier_name"]
        po_qty   = po_for_pb_validation["po_qty"]

        # EBW > qty -> net_qty negative
        self._open_pb_with_po(pb_page, supplier)
        self._fill_native(pb_page, pb_page.EMPTY_BAG_WEIGHT, po_qty + 5)
        pb_page.open_qty_details_popup(0)
        pb_page.fill_qty_details(1, po_qty)
        pb_page.click_done()
        pb_page.page.wait_for_timeout(800)
        errors = [e.inner_text().strip() for e in pb_page.page.locator("mat-error").all()]
        assert any("less than 0" in e or "cannot" in e.lower() for e in errors), (
            f"Expected net_qty/amount error after EBW > qty, got: {errors}"
        )
        self._cancel(pb_page)

        # labour > gross amount
        self._open_pb_with_po(pb_page, supplier)
        self._fill_native(pb_page, pb_page.LABOUR_CHARGES, 999999)
        pb_page.open_qty_details_popup(0)
        pb_page.fill_qty_details(1, po_qty)
        pb_page.click_done()
        pb_page.page.wait_for_timeout(800)
        errors = [e.inner_text().strip() for e in pb_page.page.locator("mat-error").all()]
        assert any(
            "less than 0" in e or "cannot" in e.lower()
            or "greater than 0" in e or "must be" in e.lower()
            for e in errors
        ), f"Expected amount error when labour > gross, got: {errors}"
        self._cancel(pb_page)

        # qty = 0 in popup
        self._open_pb_with_po(pb_page, supplier)
        pb_page.open_qty_details_popup(0)
        pb_page.fill_qty_details(1, 0)
        pb_page.page.wait_for_timeout(600)
        pb_page.page.locator(pb_page.DONE_BTN).click(force=True)
        pb_page.page.wait_for_timeout(800)
        errors      = pb_page.page.locator("mat-error").count()
        popup_open  = pb_page.page.locator(pb_page.DONE_BTN).is_visible()
        assert errors > 0 or popup_open, \
            "Expected mat-error or popup to stay open when qty=0"
        self._cancel(pb_page)

    # ── positive assertion ────────────────────────────────────────────────────

    def test_transportation_does_not_affect_total(self, pb_page, po_for_pb_validation):
        """Transportation (other charges) must not change the master Total Amount."""
        self._open_pb_with_po(pb_page, po_for_pb_validation["supplier_name"])

        pb_page.open_qty_details_popup(0)
        pb_page.fill_qty_details(1, po_for_pb_validation["po_qty"])
        pb_page.click_done()
        pb_page.page.wait_for_timeout(500)

        total_before = pb_page.read_total_amount() or 0
        pb_page.fill_other_charges(transportation=500)
        pb_page.page.wait_for_timeout(500)
        total_after = pb_page.read_total_amount() or 0

        assert abs(total_after - total_before) < 1.0, (
            f"Transportation should NOT change Total Amount: "
            f"before={total_before:.2f} after={total_after:.2f}"
        )
        print(f"\n  Total before transport: {total_before:.2f}")
        print(f"  Total after  transport: {total_after:.2f}  -> NO CHANGE (correct)")
        self._cancel(pb_page)

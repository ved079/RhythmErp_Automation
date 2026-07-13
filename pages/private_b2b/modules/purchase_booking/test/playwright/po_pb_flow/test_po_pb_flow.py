"""
PO -> PB direct flow tests (Rolex Traders tenant).

Flow: create PO -> create PB directly against it (no GP / GRN / QC).

Classes:
  TestPO_PB_DirectFlow   -- single-item PO with disc/int -> PB qty/rate/txn assertions
  TestPO_PB_MultiRow     -- 2-item PO with per-row disc/int -> PB assertions per row
  TestPO_PB_CustomRate   -- manually override PO rate -> PB must carry the new rate
  TestPO_PB_NoGST        -- PO with GST off -> PB txn = qty x rate (no tax)
  TestPOValidations      -- PO form validation rules (Rolex Traders tenant)
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

    def test_step1_create_po(self, po_page, integration_state):
        """Create a single-item PO with 5% discount and 2% interest."""
        total, row_dicts, supplier_name, location, ref_no = \
            po_page.create_record_for_integration(item_configs=[(10, 5, 2)])

        assert ref_no,        "PO ref_no must be non-empty"
        assert supplier_name, "Supplier must be captured"
        assert total > 0,     "PO total must be > 0"

        integration_state["po_ref_no"]     = ref_no
        integration_state["supplier_name"] = supplier_name
        integration_state["po_total"]      = total
        integration_state["po_rows"]       = row_dicts

        r = row_dicts[0]
        print("\n" + "=" * 60)
        print(f"  PO created:    {ref_no}")
        print(f"  Supplier:      {supplier_name}")
        print(f"  Item:          {r['item_name']}")
        print(f"  Rate:          {r['rate']:.2f}  Qty: {r['qty']}")
        print(f"  Disc%: {r['disc_pct']}  Int%: {r['int_pct']}  Txn: {r['txn_amount']:.2f}")
        print(f"  PO Total:      {total:.2f}")
        print("=" * 60)

    def test_step2_create_pb(self, pb_page, integration_state):
        """Create PB; qty/rate/txn must match PO (disc & int already baked into txn)."""
        if not integration_state.get("po_ref_no"):
            pytest.skip("PO not created in step 1")

        supplier_name = integration_state["supplier_name"]
        po_rows       = integration_state["po_rows"]

        row_configs  = [(1, int(r["qty"])) for r in po_rows]
        total_amount, pb_rows = pb_page.create_record_from_po(
            supplier_name, row_configs=row_configs
        )

        assert total_amount > 0, "PB total must be > 0"

        print("\n" + "=" * 60)
        _assert_pb_rows(po_rows, pb_rows, integration_state["po_ref_no"])

        expected_total = sum(r["txn_amount"] for r in po_rows)
        assert abs(total_amount - expected_total) < 1.0, (
            f"PB total {total_amount} != expected {expected_total}"
        )
        integration_state["pb_total"] = total_amount
        print(f"  TOTAL  expected: {expected_total:.2f}   actual: {total_amount:.2f}  -> MATCH")
        print("=" * 60)


# ── Multi-item flow (with per-row discount & interest) ────────────────────────

@pytest.mark.po_pb
class TestPO_PB_MultiRow:

    def test_step1_create_po_multi(self, po_page, integration_state):
        """Create a 2-item PO: row0 disc=5%/int=2%, row1 disc=3%/int=1%."""
        total, row_dicts, supplier_name, location, ref_no = \
            po_page.create_record_for_integration(
                item_configs=[(10, 5, 2), (5, 3, 1)]
            )

        assert ref_no,              "PO ref_no must be non-empty"
        assert len(row_dicts) == 2, f"Expected 2 PO rows, got {len(row_dicts)}"
        assert total > 0,           "PO total must be > 0"

        integration_state["po_ref_no"]     = ref_no
        integration_state["supplier_name"] = supplier_name
        integration_state["po_total"]      = total
        integration_state["po_rows"]       = row_dicts

        print("\n" + "=" * 60)
        print(f"  PO created:    {ref_no}  |  Supplier: {supplier_name}")
        for i, r in enumerate(row_dicts):
            print(f"  Row {i}: {r['item_name']:<20}  qty={r['qty']}  rate={r['rate']:.2f}"
                  f"  disc={r['disc_pct']}%  int={r['int_pct']}%  txn={r['txn_amount']:.2f}")
        print(f"  PO Total:      {total:.2f}")
        print("=" * 60)

    def test_step2_create_pb_multi(self, pb_page, integration_state):
        """Create PB for all rows; every row qty/rate/txn must match PO."""
        if not integration_state.get("po_ref_no"):
            pytest.skip("PO not created in step 1")

        supplier_name = integration_state["supplier_name"]
        po_rows       = integration_state["po_rows"]

        row_configs  = [(1, int(r["qty"])) for r in po_rows]
        total_amount, pb_rows = pb_page.create_record_from_po(
            supplier_name, row_configs=row_configs
        )

        assert total_amount > 0, "PB total must be > 0"

        print("\n" + "=" * 60)
        _assert_pb_rows(po_rows, pb_rows, integration_state["po_ref_no"])

        expected_total = sum(r["txn_amount"] for r in po_rows)
        assert abs(total_amount - expected_total) < 1.0, (
            f"PB total {total_amount} != expected {expected_total}"
        )
        integration_state["pb_total"] = total_amount
        print(f"  TOTAL  expected: {expected_total:.2f}   actual: {total_amount:.2f}  -> MATCH")
        print("=" * 60)


# ── Custom rate override flow ─────────────────────────────────────────────────
# PO rate is auto-fetched from Commodity Base Rate, but the field is a plain
# input — you can overwrite it. PB must carry the manually set rate.

@pytest.mark.po_pb
class TestPO_PB_CustomRate:

    def test_step1_create_po_with_custom_rate(self, po_page, integration_state):
        """Open PO form, let rate auto-fetch, then override it 10% lower."""
        po_page.open_add_form()
        po_page.fill_header()

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
        supplier_name = po_page.page.locator(
            "td.cdk-column-supplier_name"
        ).first.inner_text().strip()

        integration_state["po_ref_no"]     = ref_no
        integration_state["supplier_name"] = supplier_name
        integration_state["auto_rate"]     = auto_rate
        integration_state["custom_rate"]   = custom_rate
        integration_state["po_rows"] = [{
            "item_name":  item_name,
            "qty":        qty,
            "rate":       custom_rate,
            "disc_pct":   0,
            "int_pct":    0,
            "txn_amount": txn_amount,
        }]

        print("\n" + "=" * 60)
        print(f"  PO created:    {ref_no}")
        print(f"  Item:          {item_name}")
        print(f"  Auto rate:     {auto_rate:.2f}   Custom rate: {custom_rate:.2f}  (-10%)")
        print(f"  Qty:           {qty}   Txn: {txn_amount:.2f}")
        print("=" * 60)

    def test_step2_create_pb_with_custom_rate(self, pb_page, integration_state):
        """PB must carry the custom rate, not the original auto-fetched rate."""
        if not integration_state.get("po_ref_no"):
            pytest.skip("PO not created in step 1")

        supplier_name = integration_state["supplier_name"]
        po_rows       = integration_state["po_rows"]
        custom_rate   = integration_state["custom_rate"]
        auto_rate     = integration_state["auto_rate"]

        row_configs  = [(1, int(r["qty"])) for r in po_rows]
        total_amount, pb_rows = pb_page.create_record_from_po(
            supplier_name, row_configs=row_configs
        )

        assert total_amount > 0, "PB total must be > 0"
        assert pb_rows, "PB must have at least one row"

        pb_rate = pb_rows[0]["rate"]
        assert abs(pb_rate - custom_rate) < 0.01, (
            f"PB rate {pb_rate:.2f} should match custom PO rate {custom_rate:.2f}, "
            f"not auto-fetched {auto_rate:.2f}"
        )

        print("\n" + "=" * 60)
        print(f"  Auto rate:     {auto_rate:.2f}")
        print(f"  Custom rate:   {custom_rate:.2f}")
        print(f"  PB rate:       {pb_rate:.2f}  -> MATCH: {abs(pb_rate - custom_rate) < 0.01}")
        print("=" * 60)


# ── No-GST flow ───────────────────────────────────────────────────────────────
# PO created with enable_gst=False -> txn_amount = qty x rate (no tax).
# PB must match the same txn with no tax component.

@pytest.mark.po_pb
class TestPO_PB_NoGST:

    def test_step1_create_po_no_gst(self, po_page, integration_state):
        """Create PO with GST disabled; txn_amount must equal qty x rate."""
        total, row_dicts, supplier_name, location, ref_no = \
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

        integration_state["po_ref_no"]     = ref_no
        integration_state["supplier_name"] = supplier_name
        integration_state["po_rows"]       = row_dicts

        print("\n" + "=" * 60)
        print(f"  PO created:    {ref_no}  (GST OFF)")
        print(f"  Item:          {r['item_name']}")
        print(f"  Rate:          {r['rate']:.2f}  Qty: {r['qty']}")
        print(f"  Txn amount:    {r['txn_amount']:.2f}  (= rate x qty, no tax)")
        print(f"  Tax amount:    {r.get('tax_amount', 0):.2f}  (must be 0)")
        print("=" * 60)

    def test_step2_create_pb_no_gst(self, pb_page, integration_state):
        """PB txn must match PO txn with no tax added."""
        if not integration_state.get("po_ref_no"):
            pytest.skip("PO not created in step 1")

        supplier_name = integration_state["supplier_name"]
        po_rows       = integration_state["po_rows"]
        po_r          = po_rows[0]

        row_configs  = [(1, int(po_r["qty"]))]
        total_amount, pb_rows = pb_page.create_record_from_po(
            supplier_name, row_configs=row_configs
        )

        assert total_amount > 0, "PB total must be > 0"
        pb_r = pb_rows[0]

        assert abs(pb_r["rate"] - po_r["rate"]) < 0.01, (
            f"PB rate {pb_r['rate']:.2f} != PO rate {po_r['rate']:.2f}"
        )
        assert abs(pb_r["txn_amount"] - po_r["txn_amount"]) < 1.0, (
            f"PB txn {pb_r['txn_amount']:.2f} != PO txn {po_r['txn_amount']:.2f} — "
            f"tax may have been incorrectly applied"
        )

        print("\n" + "=" * 60)
        print(f"  PO txn (no GST):  {po_r['txn_amount']:.2f}")
        print(f"  PB txn:           {pb_r['txn_amount']:.2f}  -> "
              f"MATCH: {abs(pb_r['txn_amount'] - po_r['txn_amount']) < 1.0}")
        print("=" * 60)


# ── PO form validations (Rolex Traders tenant) ────────────────────────────────
# Mirror of TestPORegression / TestPOValidation from test_po_ui.py but run
# against the Rolex Traders tenant to confirm the same rules apply.

@pytest.mark.po_pb
class TestPOValidations:

    def _open_with_one_item(self, po_page):
        po_page.open_add_form()
        po_page.fill_header()
        po_page._select_random_mat_option_nth(po_page.ITEM_NAME, 0)
        po_page.page.wait_for_timeout(1500)

    def test_empty_submit_blocked(self, po_page):
        """Empty PO form submit must not close the form."""
        po_page.open_add_form()
        po_page.page.locator(po_page.SUBMIT_BTN).click(force=True)
        po_page.page.wait_for_timeout(800)
        assert po_page.page.locator(po_page.SUPPLIER_NAME).count() > 0, \
            "Empty submit must keep form open"
        po_page.close_popup()

    def test_cancel_returns_to_listing(self, po_page):
        """Cancel on open form must return to listing table."""
        po_page.open_add_form()
        po_page.close_popup()
        assert po_page.page.locator("table.mat-mdc-table").count() > 0, \
            "Listing table must be visible after cancel"

    def test_qty_zero_blocked(self, po_page):
        """Qty=0 must show mat-error and block submission."""
        self._open_with_one_item(po_page)
        po_page._fill_number_nth(po_page.QUANTITY, 0, 10)
        po_page._fill_number_nth(po_page.QUANTITY, 0, 0)
        po_page.page.locator(po_page.SUBMIT_BTN).click(force=True)
        po_page.page.wait_for_timeout(1000)
        assert po_page.page.locator("mat-error").count() > 0, \
            "mat-error must appear for qty=0"
        assert po_page.page.locator(po_page.SUPPLIER_NAME).count() > 0, \
            "Form must stay open on qty=0"
        po_page.close_popup()

    def test_qty_negative_blocked(self, po_page):
        """Negative qty must show mat-error."""
        self._open_with_one_item(po_page)
        po_page._fill_number_nth(po_page.QUANTITY, 0, -1)
        po_page.page.wait_for_timeout(600)
        assert po_page.page.locator("mat-error").count() > 0, \
            "mat-error must appear for negative qty"
        po_page.close_popup()

    def test_discount_over_100_blocked(self, po_page):
        """Discount > 100 must show mat-error."""
        self._open_with_one_item(po_page)
        po_page._fill_number_nth(po_page.QUANTITY, 0, 10)
        po_page._fill_number_nth(po_page.DISCOUNT, 0, 110)
        po_page.page.wait_for_timeout(600)
        assert po_page.page.locator("mat-error").count() > 0, \
            "mat-error must appear for discount > 100"
        po_page.close_popup()

    def test_interest_negative_blocked(self, po_page):
        """Negative interest must show 'Interest cannot be less than 0'."""
        self._open_with_one_item(po_page)
        po_page._fill_number_nth(po_page.QUANTITY, 0, 10)
        po_page._fill_number_nth(po_page.INTEREST, 0, -5)
        po_page.page.locator(po_page.SUBMIT_BTN).click(force=True)
        po_page.page.wait_for_timeout(1000)
        error = po_page.page.locator("mat-error").filter(
            has_text="Interest cannot be less than 0"
        )
        assert error.count() > 0, "Expected 'Interest cannot be less than 0' mat-error"
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

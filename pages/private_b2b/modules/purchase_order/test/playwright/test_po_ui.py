"""
Purchase Order — Playwright UI test suite
=========================================
Tests:
  1  Smoke         — create PO, verify found by Total PO Amount + workflow status
  2  Validation    — empty submit blocked + cancel returns to listing (one form open)
  3  Listing       — table has rows + bogus search returns empty
  4  Full workflow — create once → verify total → approve → verify status → verify edit disabled
  5  Multi-row     — all available items, Total PO Amount == table value
  6  View          — View action shows read-only form (no Submit/Approve)
  7  Duplicate     — same item twice triggers validation error
  8  Edit          — remove rows, add rows, ref_no unchanged, qty recalculates formula
  9  GST           — per-row GST toggle: tax_amount = txn_amount × rate%, total includes tax
"""

import pytest
import random


# ── Group 1: Smoke ─────────────────────────────────────────────────────────

@pytest.mark.smoke
class TestPOSmoke:
    def test_create_search_and_status(self, po_page):
        """Create a single-item PO (disc=2, int=5); verify calc, listing, and workflow status."""
        total, row_dicts, _, _, _ = po_page.create_record_for_integration(item_configs=[(10, 2, 5)])
        row = row_dicts[0]
        row_sum = row["txn_amount"]

        # Calc: Transaction Amount = Rate × Qty
        assert abs(row_sum - row["rate"] * row["qty"]) < 0.10, \
            f"Transaction Amount {row_sum:.2f} != Rate {row['rate']:.2f} × Qty {row['qty']}"
        # Calc: interest (5%) > discount (2%) so total must be greater than row sum
        assert total > row_sum, \
            f"Total PO Amount {total:.2f} should be > row sum {row_sum:.2f} with int=5% > disc=2%"
        # Calc: exact formula total = row_sum × (1 - disc/100 + int/100)
        expected = row_sum * (1 - row["disc_pct"] / 100 + row["int_pct"] / 100)
        assert abs(total - expected) < 0.50, \
            f"Total {total:.2f} != row_sum × (1 - {row['disc_pct']}% + {row['int_pct']}%) = {expected:.2f}"

        po_page.search_by_total_amount(total)
        assert po_page.is_po_amount_in_table(total), \
            f"PO with Total PO Amount={total} not found after creation"
        status = po_page.get_workflow_status_of_first_row()
        assert status == "Created", \
            f"Unexpected status after create: {status}"


# ── Group 2: Validation ────────────────────────────────────────────────────

@pytest.mark.validation
class TestPOValidation:
    def test_form_submit_and_cancel(self, po_page):
        """Empty submit must not close the form; Cancel must return to listing."""
        po_page.open_add_form()
        # Try submitting empty — form should stay open
        po_page.page.locator(
            "xpath=//div[contains(@class,'popup-footer')]"
            "//button[contains(@class,'mat-mdc-unelevated-button') or contains(@class,'mat-mdc-raised-button')]"
            "[.//span[contains(.,'Submit')]]"
        ).click(force=True)
        po_page.page.wait_for_timeout(800)
        assert po_page.page.locator(po_page.SUPPLIER_NAME).count() > 0, \
            "Empty form should not have closed after Submit"
        # Cancel — should return to listing
        po_page.close_popup()
        assert po_page.page.locator("table.mat-mdc-table").count() > 0, \
            "Listing table not visible after cancelling form"


# ── Group 3: Listing ───────────────────────────────────────────────────────

@pytest.mark.smoke
class TestPOListing:
    def test_listing_and_search(self, po_page):
        """Table must have rows; bogus ref-no search must return empty."""
        assert po_page.get_table_row_count() > 0, "PO listing must have at least one row"
        po_page.search_po("PUR/XXXX/9999999")
        assert not po_page.is_po_in_table("PUR/XXXX/9999999"), \
            "Bogus ref-no should not match any row"


# ── Group 4: Full workflow ─────────────────────────────────────────────────

@pytest.mark.workflow
class TestPOFullWorkflow:
    def test_full_workflow(self, po_page):
        """Create PO, verify Total PO Amount in table and workflow status is 'Created'."""
        total, row_dicts, _, _, _ = po_page.create_record_for_integration(item_configs=[(10, 5, 2)])
        row = row_dicts[0]

        # Calc: Transaction Amount = Rate × Qty
        assert abs(row["txn_amount"] - row["rate"] * row["qty"]) < 0.10, \
            f"Transaction Amount {row['txn_amount']:.2f} != Rate {row['rate']:.2f} × Qty {row['qty']}"
        # Calc: discount (5%) > interest (2%) so total must be less than row sum
        row_sum = sum(r["txn_amount"] for r in row_dicts)
        assert total < row_sum, \
            f"Total PO Amount {total:.2f} should be < row sum {row_sum:.2f} with disc=5% > int=2%"
        # Calc: exact formula total = row_sum × (1 - disc/100 + int/100)
        expected = row_sum * (1 - row["disc_pct"] / 100 + row["int_pct"] / 100)
        assert abs(total - expected) < 0.50, \
            f"Total {total:.2f} != row_sum × (1 - {row['disc_pct']}% + {row['int_pct']}%) = {expected:.2f}"

        po_page.search_by_total_amount(total)
        table_value = po_page.get_total_po_amount_of_first_row()
        assert abs(table_value - total) < 0.10, \
            f"Table Total PO Amount {table_value:.2f} != form value {total:.2f}"

        status = po_page.get_workflow_status_of_first_row()
        assert status == "Created", f"Expected 'Created' after create, got '{status}'"

        # Edit: change qty 10 → 15, verify recalculation
        new_total, new_txn = po_page.edit_first_record_qty(15)
        assert abs(new_txn - row["rate"] * 15) < 0.10, \
            f"After edit, Transaction Amount {new_txn:.2f} != Rate {row['rate']:.2f} × 15"
        assert new_total < new_txn, \
            f"After edit, Total {new_total:.2f} should be < txn {new_txn:.2f} with disc=5% > int=2%"
        po_page.search_by_total_amount(new_total)
        new_table_value = po_page.get_total_po_amount_of_first_row()
        assert abs(new_table_value - new_total) < 0.10, \
            f"Table Total PO Amount {new_table_value:.2f} != edited form value {new_total:.2f}"

    def test_multi_row_total_po_amount_matches_table(self, po_page):
        """All-items PO: form Total PO Amount must appear correctly in the listing."""
        total, rows, _, _, _ = po_page.create_record_for_integration(all_items=True)
        assert len(rows) >= 2, f"Expected at least 2 item rows, got {len(rows)}"
        assert total > 0, "Total PO Amount must be greater than 0"

        # Calc: per-row txn_amount = rate × qty for each row
        for i, r in enumerate(rows):
            assert abs(r["txn_amount"] - r["rate"] * r["qty"]) < 0.10, \
                f"Row {i}: Transaction Amount {r['txn_amount']:.2f} != Rate {r['rate']:.2f} × Qty {r['qty']}"

        # Calc: disc=0, int=0 so total == sum of row txn_amounts exactly
        row_sum = sum(r["txn_amount"] for r in rows)
        assert abs(total - row_sum) < 0.10, \
            f"Total PO Amount {total:.2f} != row sum {row_sum:.2f} with disc=0, int=0"
        # Calc: exact formula total = row_sum × (1 - 0 + 0) = row_sum
        expected = row_sum * (1 - rows[0]["disc_pct"] / 100 + rows[0]["int_pct"] / 100)
        assert abs(total - expected) < 0.10, \
            f"Total {total:.2f} != formula result {expected:.2f} with disc=0, int=0"

        po_page.search_by_total_amount(total)
        table_value = po_page.get_total_po_amount_of_first_row()
        assert abs(table_value - total) < 0.10, \
            f"Table Total PO Amount {table_value:.2f} != form value {total:.2f}"

    def test_view_popup_read_only(self, po_page):
        """View action must open read-only form with no Submit or Approve buttons."""
        po_page.click_view_button()
        po_page.verify_view_popup_read_only()
        po_page.close_popup()


# ── Group 5: Regression / Negative ────────────────────────────────────────

@pytest.mark.regression
class TestPORegression:
    def _open_form_with_one_item(self, po_page):
        """Helper: open add form, fill header, select one item. Returns to filled state."""
        po_page.open_add_form()
        po_page.fill_header()
        po_page._select_random_mat_option_nth(po_page.ITEM_NAME, 0)
        po_page.page.wait_for_timeout(1500)

    def test_qty_zero_shows_error(self, po_page):
        """Qty=0 must block submission and show an inline mat-error."""
        self._open_form_with_one_item(po_page)
        po_page._fill_number_nth(po_page.QUANTITY, 0, 10)
        po_page._fill_number_nth(po_page.DISCOUNT, 0, 5)
        po_page._fill_number_nth(po_page.INTEREST, 0, 2)
        po_page.page.wait_for_timeout(400)
        # Now overwrite qty with 0 to trigger validation on submit
        po_page._fill_number_nth(po_page.QUANTITY, 0, 0)
        po_page.page.locator(po_page.SUBMIT_BTN).click(force=True)
        po_page.page.wait_for_timeout(1000)
        assert po_page.page.locator("mat-error").count() > 0, \
            "Expected mat-error after submitting with qty=0"
        assert po_page.page.locator(po_page.SUPPLIER_NAME).count() > 0, \
            "Form must stay open on invalid qty"
        po_page.close_popup()

    def test_qty_negative_shows_error(self, po_page):
        """Negative qty must show an inline mat-error and keep the form open."""
        self._open_form_with_one_item(po_page)
        po_page._fill_number_nth(po_page.QUANTITY, 0, -1)
        po_page.page.wait_for_timeout(600)
        assert po_page.page.locator("mat-error").count() > 0, \
            "Expected mat-error for negative qty"
        assert po_page.page.locator(po_page.SUPPLIER_NAME).count() > 0, \
            "Form must stay open on negative qty"
        po_page.close_popup()

    def test_discount_over_100_shows_error(self, po_page):
        """Discount > 100 must show an inline mat-error."""
        self._open_form_with_one_item(po_page)
        po_page._fill_number_nth(po_page.QUANTITY, 0, 10)
        po_page._fill_number_nth(po_page.DISCOUNT, 0, 110)
        po_page.page.wait_for_timeout(600)
        assert po_page.page.locator("mat-error").count() > 0, \
            "Expected mat-error for discount > 100"
        assert po_page.page.locator(po_page.SUPPLIER_NAME).count() > 0, \
            "Form must stay open on invalid discount"
        po_page.close_popup()

    def test_interest_negative_shows_error(self, po_page):
        """Negative interest must block submission and show 'Interest cannot be less than 0'."""
        self._open_form_with_one_item(po_page)
        po_page._fill_number_nth(po_page.QUANTITY, 0, 10)
        po_page._fill_number_nth(po_page.DISCOUNT, 0, 5)
        po_page._fill_number_nth(po_page.INTEREST, 0, -5)
        po_page.page.locator(po_page.SUBMIT_BTN).click(force=True)
        po_page.page.wait_for_timeout(1000)
        error = po_page.page.locator("mat-error").filter(has_text="Interest cannot be less than 0")
        assert error.count() > 0, "Expected 'Interest cannot be less than 0' mat-error"
        assert po_page.page.locator(po_page.SUPPLIER_NAME).count() > 0, \
            "Form must stay open on negative interest"
        po_page.close_popup()


# ── Group 6: Duplicate item ────────────────────────────────────────────────

@pytest.mark.validation
@pytest.mark.multi_row
class TestPODuplicateItem:
    def test_same_item_twice_shows_error(self, po_page):
        """Selecting the same item in two rows must trigger a validation error."""
        po_page.open_add_form()
        po_page.fill_header()

        item_name = po_page._select_random_mat_option_nth(po_page.ITEM_NAME, 0)
        po_page.page.wait_for_timeout(500)

        po_page.page.locator(po_page.ADD_ROW_BTN).click()
        po_page.page.wait_for_timeout(600)
        po_page.page.locator(po_page.ITEM_NAME).nth(1).click(force=True)
        po_page.page.wait_for_selector(".mat-mdc-select-panel", timeout=5000)
        for opt in po_page.page.locator(".mat-mdc-select-panel mat-option span.mdc-list-item__primary-text").all():
            if opt.inner_text().strip() == item_name:
                opt.click(force=True)
                break
        po_page.page.wait_for_timeout(600)

        error = po_page.page.locator("mat-error").filter(has_text="already added")
        assert error.count() > 0, \
            f"Expected 'already added' mat-error for duplicate item '{item_name}'"
        po_page.close_popup()


# ── Group 7: Edit flow ─────────────────────────────────────────────────────
# One all-items PO is created once (class-scoped) and all 4 tests operate on it
# in sequence:  remove rows → add rows → verify ref_no unchanged → verify qty formula
#
# PO-specific twist vs GP: tests 1 and 2 also assert the listing's Total PO Amount
# went down/up after removing/adding rows — this exercises the formula end-to-end.

@pytest.fixture(scope="class")
def edit_po_state(logged_in_page):
    """Create one all-items PO (disc=0, int=0) shared across the entire TestPOEdit class."""
    from pages.private_b2b.modules.purchase_order.po_playwright_page import POPlaywrightPage
    p = POPlaywrightPage(logged_in_page)
    p.navigate_to_page()
    total, row_dicts, _, _, _ = p.create_record_for_integration(all_items=True)
    assert len(row_dicts) >= 2, "Need at least 2 items for edit tests"
    # The newly created PO is the most recent — read its ref_no from the top of the listing
    p.search_by_total_amount(total)
    ref_no = p.get_first_ref_no()
    p.navigate_to_page()
    print(f"\n[EDIT-FIXTURE] created PO {ref_no} total={total} with {len(row_dicts)} rows")
    yield ref_no, row_dicts


@pytest.mark.workflow
class TestPOEdit:
    def test_edit_remove_rows(self, po_page, edit_po_state):
        """Remove a random subset of rows; verify via View rows are gone and listing
        Total PO Amount decreased (formula check: fewer rows → lower total).

        Multi-row POs already show delete buttons — no blank-row trick needed.
        Delete in descending index order to keep lower indices stable.
        """
        ref_no, row_dicts = edit_po_state
        n = len(row_dicts)

        # Keep at most n-2 rows so at least 2 items are freed up for test_edit_add_rows
        keep_count = random.randint(1, max(1, n - 2))
        keep_indices = set(random.sample(range(n), keep_count))
        remove_indices = sorted([i for i in range(n) if i not in keep_indices], reverse=True)

        to_keep   = [row_dicts[i]["item_name"] for i in keep_indices]
        to_remove = [row_dicts[i]["item_name"] for i in range(n) if i not in keep_indices]
        print(f"\n[EDIT-REMOVE] keeping={sorted(keep_indices)}: {to_keep}")
        print(f"[EDIT-REMOVE] removing={remove_indices}: {to_remove}")

        # Read total before edit
        po_page.navigate_to_page()
        po_page.search_po(ref_no)
        total_before = po_page.get_total_po_amount_of_first_row()

        po_page.open_edit_form(0)
        for idx in remove_indices:
            po_page.delete_row_nth(idx)
        po_page.submit_update()

        # Listing total must have decreased
        po_page.navigate_to_page()
        po_page.search_po(ref_no)
        total_after = po_page.get_total_po_amount_of_first_row()
        assert total_after < total_before, \
            f"Total PO Amount should decrease after removing rows: {total_before} → {total_after}"

        # View must show only the kept items
        po_page.click_row_action(0, "View")
        po_page.page.wait_for_selector("input[readonly]", timeout=25000)
        po_page.page.wait_for_selector("span.mat-mdc-select-min-line", timeout=10000)
        po_page.page.wait_for_timeout(500)
        remaining = po_page.read_item_names_from_form()
        for item in to_keep:
            assert item in remaining, \
                f"'{item}' should still be present, got: {remaining}"
        for item in to_remove:
            assert item not in remaining, \
                f"'{item}' should have been removed but found in: {remaining}"
        po_page.navigate_to_page()

    def test_edit_add_rows(self, po_page, edit_po_state):
        """Add 2 new rows to the PO (now in reduced state from test_edit_remove_rows).

        Reads current form state first so it works regardless of how many rows remain.
        Listing Total PO Amount must increase after adding rows (formula check).
        """
        ref_no, _ = edit_po_state

        # Read total before edit
        po_page.navigate_to_page()
        po_page.search_po(ref_no)
        total_before = po_page.get_total_po_amount_of_first_row()

        po_page.open_edit_form(0)
        current_items = po_page.read_item_names_from_form()
        current_count = po_page.count_form_rows()
        print(f"\n[EDIT-ADD] current rows={current_count}: {current_items}")

        for _ in range(2):
            po_page.page.locator(po_page.ADD_ROW_BTN).click()
            po_page.page.wait_for_timeout(600)

        assert po_page.count_form_rows() == current_count + 2

        used = set(current_items)
        new_items = []
        for i in range(current_count, current_count + 2):
            rd = po_page._add_item_row(i, 10, 0, 0, used_items=used)
            if rd["item_name"]:
                used.add(rd["item_name"])
                new_items.append(rd["item_name"])

        print(f"[EDIT-ADD] added: {new_items}")
        po_page.submit_update()

        # Listing total must have increased
        po_page.navigate_to_page()
        po_page.search_po(ref_no)
        total_after = po_page.get_total_po_amount_of_first_row()
        assert total_after > total_before, \
            f"Total PO Amount should increase after adding rows: {total_before} → {total_after}"

        # View must show the new items
        po_page.click_row_action(0, "View")
        po_page.page.wait_for_selector("input[readonly]", timeout=25000)
        po_page.page.wait_for_selector("span.mat-mdc-select-min-line", timeout=10000)
        po_page.page.wait_for_timeout(500)
        all_items = po_page.read_item_names_from_form()
        for item in new_items:
            assert item in all_items, \
                f"Newly added '{item}' not found in View, got: {all_items}"
        po_page.navigate_to_page()

    def test_edit_ref_no_unchanged(self, po_page, edit_po_state):
        """PO reference number must not change after editing."""
        ref_no, _ = edit_po_state

        po_page.navigate_to_page()
        po_page.search_po(ref_no)
        po_page.open_edit_form(0)
        po_page._fill_number_nth(po_page.QUANTITY, 0, random.randint(5, 15))
        po_page.submit_update()

        po_page.navigate_to_page()
        po_page.search_po(ref_no)
        assert po_page.is_po_in_table(ref_no), \
            f"PO {ref_no} not found after edit — ref_no appears to have changed"

    def test_edit_qty_recalculates(self, po_page, edit_po_state):
        """Change qty on row 0; verify Transaction Amount = Rate × new_qty in the form
        and that the listing's Total PO Amount reflects the new value.

        This exercises the full formula chain:
            qty input → Angular recalculates txn_amount → total_po_amount updates → saved to DB → listing shows new total
        """
        ref_no, _ = edit_po_state
        new_qty = 30

        po_page.navigate_to_page()
        po_page.search_po(ref_no)
        po_page.open_edit_form(0)

        # Read the auto-populated rate for row 0 from the open edit form
        rate = po_page.read_rate_nth(0)
        assert rate > 0, "Rate must be auto-populated in edit form"

        po_page._fill_number_nth(po_page.QUANTITY, 0, new_qty)
        po_page.page.wait_for_timeout(800)

        # Transaction Amount must recalculate to rate × new_qty
        txn = po_page.read_txn_amount_nth(0)
        assert abs(txn - rate * new_qty) < 1.0, \
            f"Transaction Amount {txn:.2f} != Rate {rate:.2f} × qty {new_qty} = {rate * new_qty:.2f}"

        # Read the form-level Total PO Amount before submitting
        form_total = po_page._read_form_total_po_amount() or po_page._read_all_row_totals()
        assert form_total > 0, "Form Total PO Amount must be > 0 after qty change"

        po_page.submit_update()

        # Listing must reflect the new total
        po_page.navigate_to_page()
        po_page.search_po(ref_no)
        listing_total = po_page.get_total_po_amount_of_first_row()
        assert abs(listing_total - form_total) < 1.0, \
            f"Listing Total PO Amount {listing_total:.2f} != form value {form_total:.2f} after qty edit"


# ── Group 8: GST formula ───────────────────────────────────────────────────
# Per-row GST: toggle ON → pick random Tax Rate → Tax Amount calculates live.
# Formula:
#   tax_amount  = txn_amount × tax_rate / 100
#   row_total   = txn_amount + tax_amount
#   total_po_amount = sum(row_totals)

@pytest.mark.calculation
class TestPOGST:
    def test_gst_tax_formula(self, po_page):
        """Enable GST on every row with random tax rates; verify the formula for each row
        and that Total PO Amount equals the sum of all row totals (including tax).

        Covers:
          - tax_amount == txn_amount × tax_rate / 100  (per row)
          - row_total  == txn_amount + tax_amount       (per row)
          - total_po_amount == sum(row_totals)          (whole PO)
        """
        total, row_dicts, _, _, _ = po_page.create_record_for_integration(
            all_items=True, enable_gst=True
        )

        for i, rd in enumerate(row_dicts):
            if not rd["gst_enabled"] or rd["tax_rate"] is None:
                continue
            expected_tax  = rd["txn_amount"] * rd["tax_rate"] / 100
            expected_total = rd["txn_amount"] + expected_tax
            assert abs(rd["tax_amount"] - expected_tax) < 1.0, (
                f"Row {i} ({rd['item_name']}): "
                f"Tax Amount {rd['tax_amount']:.2f} != "
                f"txn_amount {rd['txn_amount']:.2f} × {rd['tax_rate']}% = {expected_tax:.2f}"
            )
            assert abs(rd["total_amount"] - expected_total) < 1.0, (
                f"Row {i} ({rd['item_name']}): "
                f"Row Total {rd['total_amount']:.2f} != "
                f"txn {rd['txn_amount']:.2f} + tax {rd['tax_amount']:.2f} = {expected_total:.2f}"
            )

        row_total_sum = sum(rd["total_amount"] for rd in row_dicts)
        assert abs(total - row_total_sum) < 1.0, (
            f"Total PO Amount {total:.2f} != sum of row totals {row_total_sum:.2f}"
        )


# ── Cross-check: tamper detection ─────────────────────────────────────────
# Run with -s so the input() prompt is visible.
# Flow: create PO → print expected total → PAUSE → you change DB value →
#       press Enter → script reads listing → asserts match → FAILS if tampered.

@pytest.mark.tamper_check
class TestPOTamperDetection:
    def test_po_total_matches_after_db_change(self, po_page):
        """Create a PO, print the script-calculated total, then pause so you can
        manually change txn_currency_total_amount in the DB.
        After you press Enter the script reads the listing and asserts the value
        matches what it calculated — it will FAIL if the DB was tampered with.

        Run with:  pytest ... -v -s -m tamper_check
        """
        # Single row, fixed disc/int so the formula is easy to verify manually
        qty      = 10
        disc_pct = 5
        int_pct  = 2

        total, row_dicts, _, _, ref_no = po_page.create_record_for_integration(
            item_configs=[(qty, disc_pct, int_pct)]
        )
        row = row_dicts[0]

        print("\n" + "=" * 60)
        print(f"  PO created:       {ref_no}")
        print(f"  Item:             {row['item_name']}")
        print(f"  Rate:             {row['rate']:.2f}")
        print(f"  Qty:              {qty}    Disc: {disc_pct}%    Int: {int_pct}%")
        print(f"  Form total read:  {total:.4f}  (script ground truth)")
        print("=" * 60)
        print("  >> Go change txn_currency_total_amount in the DB now.")
        print("  >> Press Enter when done to let the script verify...")
        input()

        # Create a throwaway PO → forces DB to recalculate and listing to refresh
        po_page.trigger_po_status_recalculation()
        po_page.search_po(ref_no)
        listing_total = po_page.get_total_po_amount_of_first_row()

        print(f"\n  Listing shows:    {listing_total:.4f}")
        print(f"  Script expected:  {total:.4f}")
        print("=" * 60)

        assert abs(listing_total - total) < 1.0, (
            f"TAMPER DETECTED — listing shows {listing_total:.4f} "
            f"but script recorded {total:.4f} at creation time "
            f"(diff: {abs(listing_total - total):.4f})"
        )

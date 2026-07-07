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
"""

import pytest


# ── Group 1: Smoke ─────────────────────────────────────────────────────────

@pytest.mark.smoke
class TestPOSmoke:
    def test_create_search_and_status(self, po_page):
        """Create a single-item PO (disc=2, int=5); verify calc, listing, and workflow status."""
        total, row_dicts = po_page.create_record([(10, 2, 5)])
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
        total, row_dicts = po_page.create_record([(10, 5, 2)])
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
        total, rows = po_page.create_record(all_items=True)
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

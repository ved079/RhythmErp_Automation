"""
Purchase Order — Playwright UI test suite
=========================================
Groups:
  Group 1  Smoke     — create PO, search by Total PO Amount, verify it appears
  Group 2  Validation — empty submit blocked, cancel returns to listing
  Group 3  Listing   — table not empty, search miss returns empty
  Group 4  Workflow  — approve changes status, locked after approve, view is read-only
  Group 5  Duplicate — same item in two rows triggers validation error
"""

import pytest


# ── helpers ────────────────────────────────────────────────────────────────

def _single():
    return [(10, 5, 2)]


def _multi():
    return [(10, 5, 2), (5, 0, 3)]


# ── Group 1: Smoke ─────────────────────────────────────────────────────────

@pytest.mark.smoke
class TestPOSmoke:
    def test_create_and_search(self, po_page):
        """Create a single-item PO; verify it appears in listing via Total PO Amount."""
        total, _ = po_page.create_record(_single())
        po_page.search_by_total_amount(total)
        assert po_page.is_po_amount_in_table(total), \
            f"PO with Total PO Amount={total} not found after creation"

    def test_workflow_status_after_create(self, po_page):
        """Newly created PO must be 'Pending For Approval' or 'Created'."""
        total, _ = po_page.create_record(_single())
        po_page.search_by_total_amount(total)
        status = po_page.get_workflow_status_of_first_row()
        assert status in ("Pending For Approval", "Created"), \
            f"Unexpected status after create: {status}"


# ── Group 2: Validation ────────────────────────────────────────────────────

@pytest.mark.validation
class TestPOValidation:
    def test_empty_submit_blocked(self, po_page):
        """Submitting an empty form must not navigate away from the form."""
        po_page.open_add_form()
        # Click Submit via the footer primary button — form is empty so it should block
        po_page.page.locator(
            "xpath=//div[contains(@class,'popup-footer')]"
            "//button[contains(@class,'mat-mdc-unelevated-button') or contains(@class,'mat-mdc-raised-button')]"
            "[.//span[contains(.,'Submit')]]"
        ).click(force=True)
        po_page.page.wait_for_timeout(800)
        # Supplier field still visible → form did not close
        assert po_page.page.locator(po_page.SUPPLIER_NAME).count() > 0, \
            "Empty form should not have closed after Submit"
        po_page.close_popup()

    def test_discard_popup(self, po_page):
        """Cancel closes the form and the listing table is visible."""
        po_page.open_add_form()
        po_page.close_popup()
        assert po_page.page.locator("table.mat-mdc-table").count() > 0, \
            "Listing table not visible after cancelling form"


# ── Group 3: Listing ───────────────────────────────────────────────────────

@pytest.mark.smoke
class TestPOListing:
    def test_table_has_rows(self, po_page):
        """PO listing must have at least one row."""
        assert po_page.get_table_row_count() > 0

    def test_search_nonexistent_returns_empty(self, po_page):
        """Searching a bogus ref-no must yield no results."""
        po_page.search_po("PUR/XXXX/9999999")
        assert not po_page.is_po_in_table("PUR/XXXX/9999999"), \
            "Bogus ref-no should not match any row"


# ── Group 4: Full workflow ─────────────────────────────────────────────────

@pytest.mark.workflow
class TestPOFullWorkflow:
    def test_total_po_amount_in_table_matches_form(self, po_page):
        """Total PO Amount shown in the listing must match the value read from the form."""
        total, _ = po_page.create_record(_single())
        po_page.search_by_total_amount(total)
        table_value = po_page.get_total_po_amount_of_first_row()
        assert abs(table_value - total) < 0.10, \
            f"Table Total PO Amount {table_value:.2f} doesn't match form value {total:.2f}"

    def test_multi_row_total_po_amount_matches_row_sum(self, po_page):
        """Total PO Amount must equal sum of all row totals (no discount/interest so math is exact)."""
        total, rows = po_page.create_record(all_items=True)
        assert len(rows) >= 2, f"Expected at least 2 item rows, got {len(rows)}"
        expected = sum(r["txn_amount"] for r in rows)
        assert abs(total - expected) < 0.10, \
            f"Form Total PO Amount {total:.2f} != sum of row amounts {expected:.2f}"
        po_page.search_by_total_amount(total)
        table_value = po_page.get_total_po_amount_of_first_row()
        assert abs(table_value - total) < 0.10, \
            f"Table Total PO Amount {table_value:.2f} != form value {total:.2f}"

    def test_approve_changes_status(self, po_page):
        """After approving, workflow status column must show 'Approve'."""
        total, _ = po_page.create_record(_single())
        po_page.search_by_total_amount(total)
        po_page.approve_po()
        po_page.search_by_total_amount(total)
        status = po_page.get_workflow_status_of_first_row()
        assert status == "Approve", f"Expected 'Approve' after approval, got '{status}'"

    def test_approved_po_is_locked(self, po_page):
        """Edit action must be disabled in the row menu after a PO is approved."""
        total, _ = po_page.create_record(_single())
        po_page.search_by_total_amount(total)
        po_page.approve_po()
        po_page.search_by_total_amount(total)
        assert po_page.is_edit_disabled(), "Edit must be disabled in the action menu after approval"

    def test_view_popup_read_only(self, po_page):
        """View action must open the form without a Submit button."""
        po_page.click_view_button()
        po_page.verify_view_popup_read_only()
        po_page.close_popup()


# ── Group 5: Duplicate item ────────────────────────────────────────────────

@pytest.mark.validation
@pytest.mark.multi_row
class TestPODuplicateItem:
    def test_same_item_twice_shows_error(self, po_page):
        """Selecting the same item in two rows must trigger a validation error."""
        po_page.open_add_form()
        po_page.fill_header()

        # Row 0 — pick any item
        item_name = po_page._select_random_mat_option_nth(po_page.ITEM_NAME, 0)
        po_page.page.wait_for_timeout(500)

        # Row 1 — add row, force-select the same item
        po_page.page.locator(po_page.ADD_ROW_BTN).click()
        po_page.page.wait_for_timeout(600)
        po_page.page.locator(po_page.ITEM_NAME).nth(1).click(force=True)
        po_page.page.wait_for_selector(".mat-mdc-select-panel", timeout=5000)
        # exact match to avoid substring collision
        panel_options = po_page.page.locator(".mat-mdc-select-panel mat-option span.mdc-list-item__primary-text").all()
        for opt in panel_options:
            if opt.inner_text().strip() == item_name:
                opt.click(force=True)
                break
        po_page.page.wait_for_timeout(600)

        error = po_page.page.locator("mat-error").filter(has_text="already added")
        assert error.count() > 0, \
            f"Expected 'already added' mat-error for duplicate item '{item_name}'"
        po_page.close_popup()
